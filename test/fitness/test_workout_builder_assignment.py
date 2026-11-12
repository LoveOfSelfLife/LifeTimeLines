from html.parser import HTMLParser
from pathlib import Path

import pytest
from flask import Flask, render_template


TEMPLATES = Path(__file__).resolve().parents[2] / 'services' / 'fitnessclub' / 'templates'


class AssignmentOptions(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_select = False
        self.options = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'select' and attrs.get('id') == 'assigned_member':
            self.in_select = True
        elif tag == 'option' and self.in_select:
            self.options.append(attrs)

    def handle_endtag(self, tag):
        if tag == 'select' and self.in_select:
            self.in_select = False


@pytest.mark.parametrize(('assignment', 'legacy_member', 'selected'), [
    (None, None, ''),
    ('', 'member-2', ''),
    ('member-2', None, 'member-2'),
    ('missing', None, 'missing'),
])
def test_workout_builder_shows_only_explicit_assignment(assignment, legacy_member, selected):
    app = Flask(__name__, template_folder=str(TEMPLATES))
    app.jinja_env.globals['url_for'] = lambda endpoint, **kwargs: '/workouts/action'
    workout = {'id': 'workout', 'name': 'Workout', 'assigned_to_member_id': assignment,
               'member_id': legacy_member}
    with app.app_context():
        html = render_template(
            'workouts/workout_builder2.html', workout=workout, workout_type='workout_definition',
            role_context={'role': 'coach'}, accessible_members=[
                {'id': 'member-1', 'name': 'First Member'}, {'id': 'member-2', 'name': 'Second Member'}],
            can_save_workout=True, can_delete_workout=True, editing_program_workout=False)

    parser = AssignmentOptions()
    parser.feed(html)
    chosen = [option for option in parser.options if 'selected' in option]
    assert len(chosen) == 1
    assert chosen[0]['value'] == selected
    assert 'hx-trigger="change"' in html
    if not assignment:
        assert 'disabled' in chosen[0]
        assert 'Unassigned' not in html
    if assignment == 'missing':
        assert 'Assigned member unavailable' in html
