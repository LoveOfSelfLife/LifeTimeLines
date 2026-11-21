from html.parser import HTMLParser
from pathlib import Path

import pytest
from flask import Flask, render_template
from jinja2 import ChoiceLoader, FileSystemLoader

from common.card_presentation import build_card_view
from common.fitness.exercise_card import extract_image_url
from common.fitness.exercise_entity import ExerciseEntity


ROOT = Path(__file__).resolve().parents[2]


class Elements(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.elements = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))

    def find(self, tag, **attrs):
        return [
            item for element, item in self.elements
            if element == tag and all(item.get(key) == value for key, value in attrs.items())
        ]


class ActionButtons(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.buttons = {}
        self.current = None
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "button":
            self.current = {"attrs": attrs, "text": "", "icons": []}
            self.buttons[attrs.get("aria-label")] = self.current
        elif tag == "i" and self.current is not None:
            self.current["icons"].append(attrs)

    def handle_data(self, data):
        if self.current is not None:
            self.current["text"] += data

    def handle_endtag(self, tag):
        if tag == "button":
            self.current = None


@pytest.fixture
def app():
    app = Flask(__name__)
    app.secret_key = "test"
    app.jinja_loader = ChoiceLoader([
        FileSystemLoader(str(ROOT / "services" / "fitnessclub" / "templates")),
        FileSystemLoader(str(ROOT / "common" / "templates")),
    ])
    return app


def exercise_item(**values):
    entity = ExerciseEntity({
        "id": "ex1", "name": "Bench press", "category": "strength",
        "equipment_list": ["barbell", "bench"], **values,
    })
    return {
        "entity": entity, "key": "ex1", "entity_id": "ex1",
        "is_favorite": True, "field_values": [entity["name"], entity.get("category")],
    }


def test_exercise_values_and_image_fallbacks(app):
    with app.test_request_context():
        entity = exercise_item(gif="/demo.gif", images=[{"url": "/photo.png"}])["entity"]
        card = build_card_view(entity, ExerciseEntity.card_presentation)
        assert card["title"] == "Bench press"
        assert card["image_url"] == "/demo.gif"
        assert card["fields"] == [
            {"label": "Category", "value": "strength"},
            {"label": "Equipment", "value": "barbell, bench"},
        ]
        assert extract_image_url({"gif": "", "images": [{"url": "/photo.png"}]}) == "/photo.png"
        assert build_card_view(exercise_item(gif="", images=[])["entity"],
                               ExerciseEntity.card_presentation)["image_url"] == "/static/images/exercise.png"
        legacy = exercise_item(equipment_list=[], equipment="dumbbell", category="")["entity"]
        assert build_card_view(legacy, ExerciseEntity.card_presentation)["fields"] == [
            {"label": "Equipment", "value": "dumbbell"},
        ]


def test_card_values_keep_zero_and_false_but_hide_empty():
    spec = {
        "title": lambda e: "title",
        "image": lambda e: None,
        "fields": [
            {"label": key, "value": lambda e, key=key: e[key]}
            for key in ("zero", "false", "none", "empty", "spaces", "list")
        ],
        "actions": (),
    }
    data = {"zero": 0, "false": False, "none": None, "empty": "", "spaces": " ", "list": []}
    assert build_card_view(data, spec)["fields"] == [
        {"label": "zero", "value": 0}, {"label": "false", "value": False},
    ]


@pytest.mark.parametrize("modal,multi", [(False, False), (False, True), (True, False), (True, True)])
def test_library_card_context(app, monkeypatch, modal, multi):
    from services.fitnessclub.views.exercises import exercise_routes

    monkeypatch.setattr(exercise_routes, "hx_render_template",
                        lambda template, **kwargs: render_template(template, **kwargs))
    with app.test_request_context("/exercises?target=results-area",
                                  headers={"HX-Target": "results-area"}):
        html = exercise_routes.exercise_listing_base(
            {}, "ExerciseTable", 1, 10, "card",
            {"listing_view": ["name", "category"]}, [], [exercise_item()],
            allow_multi_select=multi, selected_entity_keys=["ex1"], modal_mode=modal,
        )
    elements = Elements(html)
    assert "Bench press" in html and "strength" in html and "barbell, bench" in html
    assert elements.find("img", src="/static/images/exercise.png")
    assert elements.find("button", title="Unfavorite")
    assert bool(elements.find("input", name="selected_entity_keys", type="checkbox")) == multi
    if multi:
        checkbox = elements.find("input", name="selected_entity_keys", type="checkbox")[0]
        assert "checked" in checkbox
        assert "closest .card-header" in checkbox["hx-include"]
        assert checkbox["hx-swap"] == "none"
    assert bool(elements.find("button", **{"aria-label": "Edit Exercise"})) == (not modal and not multi)
    if not modal and not multi:
        edit = ActionButtons(html).buttons["Edit Exercise"]
        assert edit["text"].strip() == "Edit"
    assert elements.find("a", **{"hx-target": "#modals-here"})


def test_builder_exercise_card_has_post_action(app, monkeypatch):
    from services.fitnessclub.views.workouts import workout_routes

    monkeypatch.setattr(workout_routes, "get_member_id_from_user_context", lambda context: "member")
    monkeypatch.setattr(workout_routes, "get_entity_view_from_request", lambda *args, **kwargs: "card")
    monkeypatch.setattr(workout_routes, "get_filter_terms_from_request", lambda name: [])
    monkeypatch.setattr(workout_routes, "get_entities", lambda *args, **kwargs: [exercise_item()])
    monkeypatch.setattr(workout_routes, "get_entity_obj_from_entity_name", lambda name: ExerciseEntity())
    monkeypatch.setattr(workout_routes, "hx_render_template",
                        lambda template, **kwargs: render_template(template, **kwargs))
    with app.test_request_context("/builder/exercises?workout_id=w1&target=results-area",
                                  headers={"HX-Target": "results-area"}):
        html = workout_routes.exercise_listing.__wrapped__(context={})
    action = Elements(html).find("button", **{"aria-label": "Add Exercise"})[0]
    assert action["hx-post"].startswith("/workouts/builder/w1/add?entity_table=ExerciseTable&key=ex1")
    assert action["hx-target"] == "#canvas"
    assert not Elements(html).find("button", **{"aria-label": "Edit Exercise"})


def test_metadata_controls_applicable_actions_and_modal_spinner(app):
    item = exercise_item()
    with app.test_request_context():
        item["card_view"] = build_card_view(item["entity"], ExerciseEntity.card_presentation)
        html = render_template(
            "entity_results_partial.html", view="card", entity_card_view_html="entity_card_view.html",
            entities=[item], entity_name="ExerciseTable", filter_terms=[], page=1, total_pages=1,
            entities_listing_route="/list?", main_content_container="main",
            card_actions=[
                {"id": "edit", "enabled": True, "url": "/edit?", "method": "get",
                 "target": "dialog", "icon": "bi-pencil", "label": "Edit"},
                {"id": "unrelated", "enabled": True, "url": "/other?", "method": "get",
                 "target": "main", "icon": "bi-plus", "label": "Other"},
            ],
        )
    elements = Elements(html)
    edit = elements.find("button", **{"aria-label": "Edit"})[0]
    assert edit["hx-target"] == "#dialog" and edit["hx-disabled-elt"] == "this"
    assert "entity-action-loading" in edit["class"]
    assert "entity-action-spinner" in html
    assert not elements.find("button", **{"aria-label": "Other"})


def test_card_footer_renders_labels_with_optional_icons(app):
    item = exercise_item()
    with app.test_request_context():
        item["card_view"] = build_card_view(item["entity"], ExerciseEntity.card_presentation)
        html = render_template(
            "entity_results_partial.html", view="card", entity_card_view_html="entity_card_view.html",
            entities=[item], entity_name="ExerciseTable", filter_terms=[], page=1, total_pages=1,
            entities_listing_route="/list?", main_content_container="main",
            card_actions=[
                {"id": "edit", "enabled": True, "url": "/edit?", "method": "get",
                 "target": "dialog", "icon": "bi-pencil", "label": "Edit Exercise",
                 "button_label": "Edit"},
                {"id": "add_to_workout", "enabled": True, "url": "/add?", "method": "post",
                 "target": "canvas", "label": "Add Exercise"},
                {"id": "unrelated", "enabled": True, "url": "/other?", "method": "get",
                 "target": "main", "icon": "bi-plus", "label": "Other"},
            ],
        )
    buttons = ActionButtons(html).buttons
    assert "Edit" in buttons["Edit Exercise"]["text"]
    assert "Edit Exercise" not in buttons["Edit Exercise"]["text"]
    assert "bi-pencil" in buttons["Edit Exercise"]["icons"][0]["class"]
    assert "Add Exercise" in buttons["Add Exercise"]["text"]
    assert not buttons["Add Exercise"]["icons"]
    assert buttons["Edit Exercise"]["attrs"]["hx-target"] == "#dialog"
    assert "btn-light" in buttons["Edit Exercise"]["attrs"]["class"].split()
    assert "btn-light" in buttons["Add Exercise"]["attrs"]["class"].split()
    assert buttons["Edit Exercise"]["attrs"]["hx-disabled-elt"] == "this"
    assert buttons["Add Exercise"]["attrs"]["hx-post"].startswith("/add?&key=ex1")
    assert "Other" not in buttons
    assert "entity-action-loading.htmx-request > .entity-action-content" in html
    assert "card-footer d-flex flex-wrap" in html


@pytest.mark.parametrize("view_route", [None, "/exercise/view?"])
def test_card_layout_and_image_link(app, view_route):
    item = exercise_item()
    with app.test_request_context():
        item["card_view"] = build_card_view(item["entity"], ExerciseEntity.card_presentation)
        html = render_template(
            "entity_results_partial.html", view="card", entity_card_view_html="entity_card_view.html",
            entities=[item], entity_name="ExerciseTable", filter_terms=[], page=1, total_pages=1,
            entities_listing_route="/list?", main_content_container="main",
            entity_view_route=view_route, card_actions=[],
        )
    elements = Elements(html)
    title = elements.find("span", **{"class": "card-title fw-semibold"})[0]
    assert title["style"] == "font-size: 0.9rem;"
    image = elements.find("img", src="/static/images/exercise.png")[0]
    assert "max-height: 160px" in image["style"]
    assert "width: 100%" in image["style"]
    assert "object-fit: contain" in image["style"]
    assert html.index("Bench press</span>") < html.index('class="img-wrapper text-center"')
    table = elements.find("table", **{"class": "table table-sm table-borderless mb-0"})[0]
    assert "--bs-table-bg: transparent" in table["style"]
    assert "--bs-table-color: inherit" in table["style"]
    assert "table-layout: fixed" in table["style"]
    assert "width: 100%" in table["style"]
    assert "overflow-wrap: anywhere" in table["style"]
    assert len(elements.find("a", **{"hx-target": "#modals-here"})) == (2 if view_route else 0)


def test_exercise_list_view_keeps_existing_fields_and_action(app, monkeypatch):
    from services.fitnessclub.views.exercises import exercise_routes

    monkeypatch.setattr(exercise_routes, "hx_render_template",
                        lambda template, **kwargs: render_template(template, **kwargs))
    with app.test_request_context("/exercises?target=results-area",
                                  headers={"HX-Target": "results-area"}):
        html = exercise_routes.exercise_listing_base(
            {}, "ExerciseTable", 1, 10, "list",
            {"listing_view": ["name", "category"]}, [], [exercise_item()],
        )
    elements = Elements(html)
    assert "Bench press" in html and "strength" in html
    assert elements.find("button", **{"aria-label": "Edit Exercise"})
    assert not elements.find("img", src="/static/images/exercise.png")


def test_get_entities_supplies_original_entity_to_card_builder(app, monkeypatch):
    from common import entities_getter
    from common.card_presentation import build_card_views
    from common.list_presentation import listing_fields

    entity = exercise_item()["entity"]
    monkeypatch.setattr(entities_getter, "get_filtered_entities", lambda *args, **kwargs: [entity])
    monkeypatch.setattr(entities_getter, "get_all_favorite_entity_ids", lambda *args: ["ex1"])
    with app.test_request_context():
        items = entities_getter.get_entities(
            "ExerciseTable", listing_fields(ExerciseEntity.list_presentation),
            member_id="member",
        )
        cards = build_card_views(items, ExerciseEntity.card_presentation)
    assert items[0]["field_values"] == ["Bench press", "strength"]
    assert items[0]["is_favorite"]
    assert cards[0]["entity"] is entity
    assert cards[0]["card_view"]["fields"][1]["value"] == "barbell, bench"
    assert "card_view" not in items[0]
