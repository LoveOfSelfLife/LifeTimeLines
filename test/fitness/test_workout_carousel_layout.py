from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from flask import Flask, render_template
import pytest


TEMPLATES = Path(__file__).resolve().parents[2] / "services" / "fitnessclub" / "templates"


@pytest.mark.parametrize("default_section,expected", [
    ("Strength", "Strength"), ("Missing", "Warmup"), (None, "Warmup"),
])
def test_fullscreen_carousel_uses_current_or_first_nonempty_section(default_section, expected):
    app = Flask(__name__, template_folder=str(TEMPLATES))
    app.jinja_env.globals["url_for"] = lambda endpoint, **kwargs: "/example/" + endpoint
    sections = [
        {"name": "Empty", "exercises": []},
        {"name": "Warmup", "exercises": [{"id": "a"}]},
        {"name": "Strength", "exercises": [{"id": "b"}]},
    ]
    with app.test_request_context("/"):
        html = render_template(
            "workouts/workout_view.html", workout={"id": "w", "name": "My Workout"},
            workout_sections=sections, default_section=default_section,
            workout_view_preference="carousel", show_finish_button=True,
            workout_instance_key=("w", "member", "WorkoutTable"), workout_definition_key="", program={"id": "p"},
            finish_workout_url="/finish", cancel_workout_url="/cancel",
            active_workout=True, rs=lambda value: value,
        )
    assert "workout-fullscreen-view" in html
    assert 'id="sectionsAccordion"' not in html
    assert 'data-section-label="{}"'.format(expected) in html
    assert html.count('aria-current="true"') == 1
    assert 'hx-post="/finish"' in html and 'hx-post="/cancel"' in html
    assert 'hx-confirm="Are you sure you want to cancel this workout?"' in html
    assert 'hx-post="/example/workouts.toggle_carousel_view"' in html
    assert 'hx-post="/example/workouts.toggle_keep_awake"' in html
    assert html.count("workout-section-option") >= 2
    assert 'data-section-label="Empty"' in html

    section_menu = html.split('aria-labelledby="workoutSectionMenu">', 1)[1].split(
        '<div class="dropdown workout-controls-menu">', 1
    )[0]
    controls_menu = html.split('aria-labelledby="workoutControlsMenu">', 1)[1].split(
        '<div class="workout-section-stage">', 1
    )[0]
    assert section_menu.index("My Workout") < section_menu.index('data-section-label="Empty"')
    assert 'id="carouselViewSwitch"' not in section_menu
    assert 'hx-post="/finish"' not in section_menu
    assert 'data-section-label=' not in controls_menu
    assert 'id="carouselViewSwitch"' in controls_menu
    assert 'id="keepAwakeSwitch"' in controls_menu
    assert 'hx-post="/finish"' in controls_menu and 'hx-post="/cancel"' in controls_menu
    assert 'aria-label="Workout controls"' in html

    class PanelParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.urls = []

        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if "workout-section-panel" in attrs.get("class", "").split():
                self.urls.append(attrs["hx-get"])

    parser = PanelParser()
    parser.feed(html)
    assert len(parser.urls) == 3
    assert parse_qs(urlsplit(parser.urls[0]).query)["workout_instance_key"] == [
        "('w', 'member', 'WorkoutTable')"
    ]


def test_accordion_view_remains_available():
    app = Flask(__name__, template_folder=str(TEMPLATES))
    app.jinja_env.globals["url_for"] = lambda endpoint, **kwargs: "/example/" + endpoint
    with app.test_request_context("/"):
        html = render_template(
            "workouts/workout_view.html", workout={"id": "w", "name": "My Workout"},
            workout_sections=[{"name": "Warmup", "exercises": [{"id": "a"}]}],
            default_section="Warmup", workout_view_preference="accordion",
            show_finish_button=True, workout_instance_key="instance", program={"id": "p"},
            finish_workout_url="/finish", cancel_workout_url="/cancel",
            active_workout=True, rs=lambda value: value,
        )
    assert 'id="sectionsAccordion"' in html
    assert 'class="workout-fullscreen-view"' not in html
    assert 'hx-post="/finish"' in html and 'hx-post="/cancel"' in html


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
