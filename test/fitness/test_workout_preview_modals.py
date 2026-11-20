from pathlib import Path

from jinja2 import Environment, FileSystemLoader


TEMPLATES = Path(__file__).resolve().parents[2] / "services" / "fitnessclub" / "templates"


def render_modal(name, **context):
    env = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=True)
    env.globals["url_for"] = lambda endpoint, filename: "/static/" + filename
    return env.get_template("home/modals/" + name).render(**context)


def test_both_modals_render_shared_exercises_and_parameters():
    sections = [{
        "name": "Strength",
        "items": [
            {"exercise": {"id": "gif", "name": "Squat", "gif": "/squat.gif"},
             "param_list": [{"type": "var", "value": 3}, {"type": "text", "value": " sets"}]},
            {"exercise": {"id": "image", "name": "Press", "images": [{"url": "/press.jpg"}]},
             "param_list": [{"type": "var", "value": None}]},
            {"exercise": {"id": "fallback", "name": "Row"},
             "param_list": [{"type": "var", "value": ""}]},
        ],
    }]
    context = {
        "workout_name": "Morning workout",
        "workout_sections": sections,
        "workout_instance": {"member_feedback": "Felt <strong>"},
        "start_time": "Nov 20, 2026 09:00 AM",
        "end_time": "Nov 20, 2026 10:00 AM",
    }

    for template in ("workout_preview_modal.html", "completed_workout_details_modal.html"):
        html = render_modal(template, **context)
        assert "Strength" in html
        assert "3 exercises" in html
        assert 'src="/squat.gif"' in html
        assert 'src="/press.jpg"' in html
        assert 'src="/static/images/exercise.png"' in html
        for exercise in ("Squat", "Press", "Row"):
            assert exercise in html
        assert '<span class="param-value">3</span>' in html
        assert '<span class="param-text"> sets</span>' in html
        assert html.count('<span class="param-value">____</span>') == 2
        assert "toggleExerciseDetails('gif'," in html

    completed = render_modal("completed_workout_details_modal.html", **context)
    assert "Started" in completed and context["start_time"] in completed
    assert "Finished" in completed and context["end_time"] in completed
    assert "Feedback" in completed and "Felt &lt;strong&gt;" in completed


def test_empty_workout_and_missing_completion_details():
    preview = render_modal("workout_preview_modal.html", workout_name="Empty", workout_sections=[])
    assert "No exercise details were found for this workout." in preview

    completed = render_modal(
        "completed_workout_details_modal.html",
        workout_name="Empty",
        workout_sections=[],
        workout_instance={},
        start_time=None,
        end_time=None,
    )
    assert "No exercise details were found for this completed workout." in completed
    assert completed.count(">Unknown</span>") == 2
    assert "Feedback" not in completed
