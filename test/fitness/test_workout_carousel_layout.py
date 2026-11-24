from pathlib import Path

from flask import Flask, render_template


TEMPLATES = Path(__file__).resolve().parents[2] / "services" / "fitnessclub" / "templates"


def test_carousel_places_parameters_before_media_and_keeps_timer():
    app = Flask(__name__, template_folder=str(TEMPLATES))
    app.jinja_env.globals["url_for"] = lambda endpoint, **kwargs: "/example"
    parameters = [
        {"type": "var", "param": "T", "value": "30", "wkout_id": "w", "ex_id": "e"},
        {"type": "text", "param": "Tu", "value": "sec"},
    ]
    with app.test_request_context("/"):
        html = render_template(
            "workouts/_section_dynamic_carousel_view.html",
            section={"name": "Main", "exercises": [{"id": "e"}]},
            exercises={"e": {"id": "e", "name": "Plank", "gif": "/plank.gif"}},
            exercise_parameters={"e": {"param_list": parameters}},
            workout={"id": "w"}, rs=lambda value: value,
            default_exercise_index=None, active_workout=True,
            workout_instance_key="workout", can_edit_parameters=True,
        )

    assert html.index("Plank</h5>") < html.index('class="workout-carousel-parameters')
    assert html.index('class="workout-carousel-parameters') < html.index('class="workout-carousel-media')
    assert 'id=param-w-e-T' in html
    assert 'id="timer-e">30s' in html
    assert 'src="/plank.gif"' in html
    assert 'data-bs-slide="prev"' in html and 'data-bs-slide="next"' in html
