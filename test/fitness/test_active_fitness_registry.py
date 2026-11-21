import pytest
from flask import Flask, render_template
from jinja2 import ChoiceLoader, FileSystemLoader
from pathlib import Path

from common import entities_getter
from common import member_entity
from common.fitness import facets as registry
from common.fitness import fitness_presentation
from common.fitness.exercise_entity import ExerciseEntity, exercise_facets
from common.fitness.member_program_entity import MemberProgramsEntity
from common.fitness.member_workout_entity import MemberWorkoutDefinitionEntity, MemberWorkoutInstanceEntity
from common.list_presentation import listing_fields
from common.member_entity import MemberEntity


@pytest.mark.parametrize("entity,expected", [
    (ExerciseEntity({"id": "ex", "name": "Press", "category": "strength"}), ["Press", "strength"]),
    (MemberProgramsEntity({"id": "p", "name": "Program", "start_date": "2026-01-01",
                           "end_date": "2026-03-01", "assigned_to_member_id": "m"}),
     ["Program", "2026-01-01", "2026-03-01", "Alex"]),
    (MemberWorkoutDefinitionEntity({"id": "w", "name": "Workout", "assigned_to_member_id": "m",
                                    "member_program_id": "p"}),
     ["Workout", "Alex", "Strength"]),
    (MemberWorkoutInstanceEntity({"id": "i", "member_id": "m", "name": "History",
                                  "started_ts": "2026-02-01T10:00:00", "member_program_id": "p"}),
     ["History", "2026-02-01", "Strength"]),
    (MemberEntity({"id": "m", "app": "club", "name": "Alex", "short_name": "A",
                   "email": "a@example.test", "role": "coach"}),
     ["Alex", "A", "a@example.test", "coach"]),
])
def test_entity_list_fields_and_favorite_state(entity, expected, monkeypatch):
    monkeypatch.setattr(member_entity, "get_member_name_from_member_id", lambda member_id: "Alex")
    monkeypatch.setattr(fitness_presentation, "get_program_name_from_program_id", lambda program_id: "Strength")
    monkeypatch.setattr(entities_getter, "get_filtered_entities", lambda *args, **kwargs: [entity])
    monkeypatch.setattr(entities_getter, "get_all_favorite_entity_ids", lambda *args: [entity.get_key_value()])

    fields = listing_fields(type(entity).list_presentation)
    assert "card_view" not in fields
    result = entities_getter.get_entities(entity.get_table_name(), fields, member_id="m")[0]
    assert result["field_values"] == expected
    assert result["card_view_fields"] is None
    assert result["entity"] is entity and result["is_favorite"]


def test_exercise_registry_preserves_facets():
    assert registry.get_fitnessclub_facets_for_entity("ExerciseTable") is exercise_facets
    assert registry.get_fitnessclub_facets_for_entity("MissingTable") is None


@pytest.mark.parametrize("entity,labels,values", [
    (ExerciseEntity({"id": "ex"}), ["name", "category"], ["", None]),
    (MemberProgramsEntity({"id": "p", "member_id": "m"}),
     ["name", "start", "end", "client"], [None, "", "", ""]),
    (MemberWorkoutDefinitionEntity({"id": "w", "member_id": "m"}),
     ["name", "client", "program"], [None, "", ""]),
    (MemberWorkoutInstanceEntity({"id": "i", "member_id": "m"}),
     ["name", "date", "program"], [None, "", ""]),
    (MemberEntity({"id": "m", "app": "club"}),
     ["name", "short_name", "email", "role"], ["", "", None, ""]),
])
def test_missing_values_and_column_order(entity, labels, values, monkeypatch):
    monkeypatch.setattr(entities_getter, "get_filtered_entities", lambda *args, **kwargs: [entity])
    fields = listing_fields(type(entity).list_presentation)
    assert fields["listing_view"] == labels
    result = entities_getter.get_entities(entity.get_table_name(), fields)[0]
    assert result["field_values"] == values


def test_client_fallback_is_distinct_for_cards(monkeypatch):
    from common.card_presentation import build_card_view

    monkeypatch.setattr(member_entity, "get_member_name_from_member_id", lambda member_id: "Alex")
    entity = MemberProgramsEntity({"id": "p", "member_id": "m"})
    assert listing_fields(entity.list_presentation)["field_mapping"]["client"](entity) == ""
    from flask import Flask
    with Flask(__name__).test_request_context():
        card = build_card_view(entity, entity.card_presentation)
    assert {"label": "Client", "value": "Alex"} in card["fields"]


@pytest.mark.parametrize("entity,labels,values", [
    (ExerciseEntity({"id": "ex", "name": "Press", "category": "strength"}),
     ["name", "category"], ["Press", "strength"]),
    (MemberProgramsEntity({"id": "p", "name": "Program", "start_date": "2026-01-01"}),
     ["name", "start", "end", "client"], ["Program", "2026-01-01", "", ""]),
    (MemberWorkoutDefinitionEntity({"id": "w", "name": "Workout"}),
     ["name", "client", "program"], ["Workout", "", ""]),
    (MemberWorkoutInstanceEntity({"id": "i", "member_id": "m", "name": "History",
                                  "started_ts": "2026-02-01T10:00:00"}),
     ["name", "date", "program"], ["History", "2026-02-01", ""]),
    (MemberEntity({"id": "m", "app": "club", "name": "Alex", "short_name": "A",
                   "email": "a@example.test", "role": "coach"}),
     ["name", "short_name", "email", "role"], ["Alex", "A", "a@example.test", "coach"]),
])
def test_listing_metadata_renders_headers_values_and_view_link(entity, labels, values, monkeypatch):
    from html.parser import HTMLParser

    class TableCells(HTMLParser):
        def __init__(self):
            super().__init__()
            self.tag = None
            self.headers = []
            self.values = []

        def handle_starttag(self, tag, attrs):
            if tag in ("th", "td"):
                self.tag = tag

        def handle_data(self, data):
            if self.tag == "th" and data.strip():
                self.headers.append(data.strip())
            elif self.tag == "td" and data.strip():
                self.values.append(data.strip())

        def handle_endtag(self, tag):
            if tag == self.tag:
                self.tag = None

    root = Path(__file__).resolve().parents[2]
    app = Flask(__name__)
    app.jinja_loader = ChoiceLoader([
        FileSystemLoader(str(root / "services" / "fitnessclub" / "templates")),
        FileSystemLoader(str(root / "common" / "templates")),
    ])
    monkeypatch.setattr(entities_getter, "get_filtered_entities", lambda *args, **kwargs: [entity])
    fields = listing_fields(type(entity).list_presentation)
    with app.test_request_context():
        rows = entities_getter.get_entities(entity.get_table_name(), fields)
        html = render_template(
            "entity_results_partial.html", view="list", entities=rows, entity_name=entity.get_table_name(),
            fields_to_display=fields, filter_terms=[], entity_view_route="/preview?",
            entities_listing_route="/list?", page=1, total_pages=1,
        )
    cells = TableCells()
    cells.feed(html)
    assert cells.headers == labels
    assert cells.values == [value for value in values if value]
    assert 'hx-get="/preview?&key=' in html and 'hx-target="#modals-here"' in html


def test_generic_get_entities_still_supports_explicit_legacy_cards(monkeypatch):
    entity = ExerciseEntity({"id": "ex", "name": "Press"})
    monkeypatch.setattr(entities_getter, "get_filtered_entities", lambda *args, **kwargs: [entity])
    fields = {
        "listing_view": ["name"], "card_view": ["title"],
        "field_mapping": {"title": lambda e: e["name"]},
    }
    result = entities_getter.get_entities("ExerciseTable", fields)[0]
    assert result["card_view_fields"] == {"title": "Press"}
