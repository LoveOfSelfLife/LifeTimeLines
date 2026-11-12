import re
from html.parser import HTMLParser
from pathlib import Path

from jinja2 import Environment, FileSystemLoader


TEMPLATES = Path(__file__).resolve().parents[2] / "services" / "fitnessclub" / "templates"


class AccordionParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.buttons = []
        self.panels = []
        self.parents = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = attrs.get("class", "").split()
        if tag == "button" and "accordion-button" in classes:
            self.buttons.append(attrs)
        elif tag == "div" and "accordion-collapse" in classes:
            self.panels.append(attrs)
        elif tag == "div" and "accordion" in classes:
            self.parents.append(attrs)


def test_program_workout_accordion_targets_are_unique_and_selector_safe():
    template = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=True).get_template(
        "workouts/workout_view2.html"
    )
    sections = [
        {"name": "Empty", "exercises": []},
        {"name": "Warmup", "exercises": [1]},
        {"name": "Strength A", "exercises": [1] * 7},
        {"name": "Strength A", "exercises": [1]},
        {"name": "Cool down / stretch", "exercises": [1]},
    ]
    parser = AccordionParser()
    for workout_id in ("baa8e81d-0ba4-4b61-9249-cec8630e00c4", "second-workout"):
        html = template.render(workout={"id": workout_id}, workout_sections=sections)
        assert "Strength A (7)" in html
        parser.feed(html)

    assert len(parser.buttons) == len(parser.panels) == 8
    panel_ids = [panel["id"] for panel in parser.panels]
    parent_ids = [parent["id"] for parent in parser.parents]
    assert len(set(panel_ids)) == len(panel_ids)
    assert len(set(parent_ids)) == len(parent_ids)
    for i, (button, panel) in enumerate(zip(parser.buttons, parser.panels)):
        assert re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", panel["id"])
        assert button["data-bs-target"] == "#" + panel["id"]
        assert button["aria-controls"] == panel["id"]
        assert panel["data-bs-parent"] == "#" + parent_ids[i // 4]
        assert button["aria-expanded"] == ("true" if i % 4 == 0 else "false")
        assert ("show" in panel["class"].split()) == (i % 4 == 0)
