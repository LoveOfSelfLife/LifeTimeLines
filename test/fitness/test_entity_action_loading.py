from html.parser import HTMLParser
from pathlib import Path

import pytest
from flask import Flask, render_template
from jinja2 import ChoiceLoader, FileSystemLoader


ROOT = Path(__file__).resolve().parents[2]


class ButtonParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.buttons = []
        self.current = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'button':
            self.current = {'attrs': attrs, 'spinner': False}
            self.buttons.append(self.current)
        elif self.current and 'entity-action-spinner' in attrs.get('class', '').split():
            self.current['spinner'] = True

    def handle_endtag(self, tag):
        if tag == 'button':
            self.current = None


@pytest.mark.parametrize('view,card_template', [
    ('list', None),
    ('card', None),
    ('card', 'program_card_view.html'),
    ('card', 'workout_card_view.html'),
    ('card', 'exercise_card_view.html'),
])
@pytest.mark.parametrize('target,has_spinner', [
    ('modals-here', True), ('dialog', True), ('entities-container', False),
])
def test_action_spinner_only_for_modal_targets(view, card_template, target, has_spinner):
    app = Flask(__name__)
    app.jinja_loader = ChoiceLoader([
        FileSystemLoader(str(ROOT / 'services' / 'fitnessclub' / 'templates')),
        FileSystemLoader(str(ROOT / 'common' / 'templates')),
    ])
    entity = {
        'entity_id': 'one', 'key': 'one', 'field_values': ['One'], 'is_favorite': False,
        'card_view_fields': {'title': 'One', 'subtitle': '', 'description': '', 'member_name': ''},
    }
    with app.test_request_context():
        html = render_template(
            'entity_results_partial.html', view=view, entity_card_view_html=card_template,
            entities=[entity], entity_name='test', filter_terms=[], fields_to_display={'listing_view': ['Name']},
            entity_action_route='/action?', entity_action_label='Open action', entity_action_icon='bi-pencil',
            entity_action_route_target=target, main_content_container='entities-container',
            entities_listing_route='/list?', page=1, total_pages=1,
        )
    parser = ButtonParser()
    parser.feed(html)
    action = next(b for b in parser.buttons if b['attrs'].get('aria-label') == 'Open action')
    assert action['spinner'] is has_spinner
    assert (action['attrs'].get('hx-disabled-elt') == 'this') is has_spinner


def test_second_list_action_gets_its_own_modal_spinner():
    app = Flask(__name__, template_folder=str(ROOT / 'common' / 'templates'))
    with app.test_request_context():
        html = render_template(
            'entity_results_partial.html', view='list', entities=[{
                'entity_id': 'one', 'key': 'one', 'field_values': ['One'], 'is_favorite': False,
            }], entity_name='test', filter_terms=[], fields_to_display={'listing_view': ['Name']},
            entity_action_route='/edit?', entity_action_label='Edit', entity_action_icon='bi-pencil',
            entity_action2_route='/analyze?', entity_action2_label='Analyze', entity_action2_icon='bi-bar-chart',
            entity_action2_route_target='modals-here', main_content_container='entities-container',
            entities_listing_route='/list?', page=1, total_pages=1,
        )
    parser = ButtonParser()
    parser.feed(html)
    actions = {b['attrs'].get('aria-label'): b for b in parser.buttons}
    assert not actions['Edit']['spinner']
    assert actions['Analyze']['spinner']
    assert actions['Analyze']['attrs']['hx-disabled-elt'] == 'this'
