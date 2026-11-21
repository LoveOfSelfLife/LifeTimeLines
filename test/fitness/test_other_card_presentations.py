from pathlib import Path
from html.parser import HTMLParser

import pytest
from flask import Flask, render_template
from jinja2 import ChoiceLoader, FileSystemLoader

from common.card_presentation import build_card_view
from common.fitness.member_program_entity import MemberProgramsEntity
from common.fitness.member_workout_entity import MemberWorkoutDefinitionEntity, MemberWorkoutInstanceEntity
from common.member_entity import MemberEntity


ROOT = Path(__file__).resolve().parents[2]


class ButtonText(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.buttons = {}
        self.label = None
        self.in_content = False
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "button":
            self.label = attrs.get("aria-label")
        elif tag == "span" and attrs.get("class") == "entity-action-content":
            self.in_content = True

    def handle_data(self, data):
        if self.label and self.in_content:
            self.buttons[self.label] = self.buttons.get(self.label, "") + data

    def handle_endtag(self, tag):
        if tag == "span" and self.in_content:
            self.in_content = False
        if tag == "button":
            self.label = None


@pytest.fixture
def app():
    app = Flask(__name__)
    app.secret_key = "test"
    app.jinja_loader = ChoiceLoader([
        FileSystemLoader(str(ROOT / "services" / "fitnessclub" / "templates")),
        FileSystemLoader(str(ROOT / "common" / "templates")),
    ])
    return app


def item(entity):
    return {
        "entity": entity,
        "entity_id": entity.get_key_value(),
        "key": entity.get_composite_key(),
        "field_values": [entity.get("name")],
        "is_favorite": True,
    }


def render_partial(template, **kwargs):
    return render_template("entity_results_partial.html", **kwargs)


def fake_url_for(endpoint, **kwargs):
    return "/" + endpoint + "?" + "&".join(f"{key}={value}" for key, value in kwargs.items())


def test_metadata_resolves_values_and_missing_fields(app, monkeypatch):
    from common import member_entity
    from common.fitness import fitness_presentation

    monkeypatch.setattr(member_entity, "get_member_name_from_member_id", lambda member_id: "Alex")
    monkeypatch.setattr(fitness_presentation, "get_program_name_from_program_id", lambda program_id: "Strength")
    with app.test_request_context():
        program = build_card_view(
            MemberProgramsEntity({"name": "Program", "start_date": "2026-01-01",
                                  "end_date": "2026-03-01", "assigned_to_member_id": "m1"}),
            MemberProgramsEntity.card_presentation,
        )
        workout = build_card_view(
            MemberWorkoutDefinitionEntity({"name": "Workout", "assigned_to_member_id": "m1",
                                           "member_program_id": "p1"}),
            MemberWorkoutDefinitionEntity.card_presentation,
        )
        history = build_card_view(
            MemberWorkoutInstanceEntity({"name": "Workout", "started_ts": "2026-02-01T10:00:00",
                                         "member_program_id": "p1"}),
            MemberWorkoutInstanceEntity.card_presentation,
        )
        member = build_card_view(
            MemberEntity({"name": "Alex", "email": "alex@example.test", "role": "coach"}),
            MemberEntity.card_presentation,
        )
    assert program["image_url"] == "/static/images/program.png"
    assert program["fields"] == [
        {"label": "Start", "value": "2026-01-01"}, {"label": "End", "value": "2026-03-01"},
        {"label": "Client", "value": "Alex"},
    ]
    assert workout["image_url"] == "/static/images/exercise_workout.png"
    assert workout["fields"] == [
        {"label": "Client", "value": "Alex"}, {"label": "Program", "value": "Strength"},
    ]
    assert history["fields"] == [
        {"label": "Date", "value": "2026-02-01"}, {"label": "Program", "value": "Strength"},
    ]
    assert member["image_url"] is None
    assert member["fields"] == [
        {"label": "Email", "value": "alex@example.test"}, {"label": "Role", "value": "coach"},
    ]


def test_program_card_has_edit_and_analyze(app, monkeypatch):
    from services.fitnessclub.views.program import programs_routes

    monkeypatch.setattr(programs_routes, "url_for", fake_url_for)
    monkeypatch.setattr(programs_routes, "hx_render_template", render_partial)
    with app.test_request_context("/programs"):
        html = programs_routes.program_listing_base(
            {}, "MemberProgramsTable", 1, 10, "card", {"listing_view": ["name"]}, [],
            [item(MemberProgramsEntity({"id": "p1", "name": "Program", "start_date": "2026-01-01"}))],
        )
    assert 'aria-label="Edit Program"' in html
    assert 'aria-label="Analyze Program"' in html
    labels = ButtonText(html).buttons
    assert labels["Edit Program"].strip() == "Edit"
    assert labels["Analyze Program"].strip() == "Analyze"
    assert 'hx-target="#modals-here"' in html
    assert "entity-action-spinner" in html
    assert "2026-01-01" in html and "Unfavorite" in html


@pytest.mark.parametrize("view,multi,modal", [
    ("card", False, False), ("list", False, False), ("card", True, False), ("card", False, True),
])
def test_workout_library_actions(app, monkeypatch, view, multi, modal):
    from services.fitnessclub.views.workouts import workout_routes

    monkeypatch.setattr(workout_routes, "url_for", fake_url_for)
    monkeypatch.setattr(workout_routes, "hx_render_template", render_partial)
    with app.test_request_context("/workouts"):
        html = workout_routes.workouts_listing_base(
            {}, "MemberWorkoutDefinitionTable", 1, None, view, {"listing_view": ["name"]}, [],
            [item(MemberWorkoutDefinitionEntity({"id": "w1", "name": "Day A"}))],
            allow_multi_select=multi, selected_entity_keys=["('w1', 'workout', 'MemberWorkoutDefinitionTable')"],
            modal_mode=modal,
        )
    assert ('aria-label="Edit Workout"' in html) == (not multi and (not modal or view == "list"))
    assert ('aria-label="Analyze Workout"' in html) == (not multi and not modal)
    if multi:
        assert 'name="selected_entity_keys"' in html and "checked" in html
    if view == "card" and not multi and not modal:
        labels = ButtonText(html).buttons
        assert labels["Edit Workout"].strip() == "Edit"
        assert labels["Analyze Workout"].strip() == "Analyze"
        assert 'hx-get="/program_analysis.report?scope=workout&key=' in html
        assert 'hx-target="#modals-here"' in html
        assert "entity-action-spinner" in html


@pytest.mark.parametrize("multi,modal,visible", [(False, False, True), (True, False, False), (False, True, False)])
def test_program_builder_workout_action(app, monkeypatch, multi, modal, visible):
    from services.fitnessclub.views.program import programs_routes

    monkeypatch.setattr(programs_routes, "url_for", fake_url_for)
    monkeypatch.setattr(programs_routes, "hx_render_template", render_partial)
    with app.test_request_context("/program/workouts-listing"):
        html = programs_routes.workouts_listing_base(
            {}, "MemberWorkoutDefinitionTable", "p1", 1, None, "card", 10,
            {"listing_view": ["name"]}, None, [],
            [item(MemberWorkoutDefinitionEntity({"id": "w1", "name": "Day A"}))],
            allow_multi_select=multi, modal_mode=modal,
        )
    assert ('aria-label="Import Workout"' in html) == visible
    if visible:
        assert ButtonText(html).buttons["Import Workout"].strip() == "Import Workout"
        assert 'hx-post="/program/builder/p1/add?entity_table=MemberWorkoutDefinitionTable&key=' in html
        assert 'hx-target="#program-canvas"' in html


@pytest.mark.parametrize("context", ["library", "builder"])
def test_workout_modal_renders_shared_card_and_selection(app, monkeypatch, context):
    from services.fitnessclub.views.program import programs_routes
    from services.fitnessclub.views.workouts import workout_routes

    routes = workout_routes if context == "library" else programs_routes
    monkeypatch.setattr(routes, "url_for", fake_url_for)
    monkeypatch.setattr(routes, "hx_render_template",
                        lambda template, **kwargs: render_template(template, **kwargs))
    workout = item(MemberWorkoutDefinitionEntity({"id": "w1", "name": "Day A"}))
    with app.test_request_context("/workouts/modal"):
        if context == "library":
            html = routes.workouts_listing_base(
                {}, "MemberWorkoutDefinitionTable", 1, None, "card", {"listing_view": ["name"]},
                [], [workout], allow_multi_select=True, selected_entity_keys=[str(workout["key"])],
                modal_mode=True,
            )
        else:
            html = routes.workouts_listing_base(
                {}, "MemberWorkoutDefinitionTable", "p1", 1, None, "card", 10,
                {"listing_view": ["name"]}, None, [], [workout], allow_multi_select=True,
                selected_entity_keys=[str(workout["key"])], modal_mode=True,
            )
    assert "modal-dialog" in html and "Day A" in html
    assert 'type="checkbox"' in html and "checked" in html
    assert 'aria-label="Edit Workout"' not in html
    assert 'aria-label="Analyze Workout"' not in html
    assert 'aria-label="Import Workout"' not in html
    assert "Add Selected Workouts" in html


def test_workout_history_card(app, monkeypatch):
    from services.fitnessclub.views.workouts import workout_routes

    monkeypatch.setattr(workout_routes, "url_for", fake_url_for)
    monkeypatch.setattr(workout_routes, "hx_render_template", render_partial)
    with app.test_request_context("/workouts/history"):
        html = workout_routes.workouts_history_listing_base(
            {}, "MemberWorkoutInstanceTable", 1, None, "card", {"listing_view": ["name"]}, [],
            [item(MemberWorkoutInstanceEntity({"id": "w1", "member_id": "m1",
                                               "name": "Day A", "started_ts": "2026-02-01T10:00:00"}))],
        )
    assert "2026-02-01" in html
    assert 'aria-label="Edit Workout"' in html
    assert ButtonText(html).buttons["Edit Workout"].strip() == "Edit"
    assert "/home.completed_workout_details_modal?" in html


@pytest.mark.parametrize("module_name", [
    "services.fitnessclub.views.admin.admin_routes",
    "services.lifetimelines.views.admin.admin_routes",
])
@pytest.mark.parametrize("view", ["card", "list"])
def test_member_admin_cards_and_lists(app, monkeypatch, module_name, view):
    from importlib import import_module

    routes = import_module(module_name)
    monkeypatch.setattr(routes, "hx_render_template", render_partial)
    with app.test_request_context("/admin/members"):
        html = routes.render_member_listing_template(
            {}, "MemberTable", 1, view, 10, {"listing_view": ["name"]}, [],
            [item(MemberEntity({"id": "m1", "app": "club", "name": "Alex",
                                "email": "alex@example.test", "role": "coach"}))],
        )
    assert "Alex" in html and 'aria-label="Edit"' in html
    assert "Unfavorite" in html
    if view == "card":
        assert "alex@example.test" in html and "coach" in html
        assert "entity_card_view.html" not in html
    else:
        assert "alex@example.test" not in html
