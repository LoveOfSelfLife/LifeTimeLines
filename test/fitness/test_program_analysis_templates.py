"""Renders the program analysis templates through the real blueprint, with the entity store and auth stubbed out."""
import os
import sys
from io import BytesIO

import pytest

flask = pytest.importorskip('flask')

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SERVICE_DIR = os.path.join(ROOT, 'services', 'fitnessclub')

from test_program_analysis import EXERCISES, WORKOUTS  # noqa: E402


class _Resp:
    def __init__(self, resp, data, js):
        self.status_code, self.headers, self.data, self.json = resp.status_code, resp.headers, data, js

    def get_data(self, as_text=False):
        return self.data.decode('utf-8') if as_text else self.data


class _Client:
    def __init__(self, app):
        self.app = app

    def get(self, url):
        with self.app.test_request_context(url):
            resp = self.app.make_response(self.app.full_dispatch_request())
            resp.direct_passthrough = False
            return _Resp(resp, resp.get_data(), resp.get_json(silent=True))


@pytest.fixture
def client(monkeypatch):
    monkeypatch.syspath_prepend(SERVICE_DIR)
    from common.fitness.program_analysis import extract
    from common.fitness.program_analysis.objectives import ProgramObjectiveEntity
    from common.auth import auth
    monkeypatch.setattr(auth, 'login_required', lambda f: f, raising=False)
    sys.modules.pop('views.program_analysis.program_analysis_routes', None)
    from views.program_analysis import program_analysis_routes as routes

    program = {'id': 'prog1', 'name': 'Test Program', 'created_by': 'm1'}
    stored = ProgramObjectiveEntity({'id': 'obj_1', 'name': 'Upper focus', 'created_by': 'm1',
                                     'rules': [{'dimension': 'pattern', 'key': 'PULL-VERT', 'min': 2}]})
    monkeypatch.setattr(routes.auth, 'login_required', lambda f: f, raising=False)
    monkeypatch.setattr(routes, '_member_id', lambda context: 'm1')
    monkeypatch.setattr(routes, '_load_program', lambda member_id, pid: program)
    monkeypatch.setattr(routes, '_all_objectives', lambda: [routes.balanced_objective(), dict(stored)])
    monkeypatch.setattr(routes, '_objective_by_id',
                        lambda oid: routes.balanced_objective() if oid == 'builtin-balanced' else (dict(stored) if oid == 'obj_1' else None))
    monkeypatch.setattr(routes, 'load_program_rows',
                        lambda p: extract.flatten_program(WORKOUTS, EXERCISES))
    monkeypatch.setattr(routes, 'load_workout_rows',
                        lambda workouts: extract.flatten_program(workouts, EXERCISES))
    monkeypatch.setattr(routes, 'get_entity',
                        lambda table, key: next((w for w in WORKOUTS if w['id'] == key), None))
    monkeypatch.setattr(routes, 'filter_entities_by_member_role', lambda member_id, entities: entities)
    monkeypatch.setattr(routes, 'hx_render_template', lambda template, **kw: flask.render_template(template, **kw))

    app = flask.Flask(__name__, template_folder=os.path.join(SERVICE_DIR, 'templates'))
    app.register_blueprint(routes.bp, url_prefix='/program_analysis')
    return _Client(app)


def test_report_renders_with_objective(client):
    r = client.get('/program_analysis/report?program_id=prog1&objective_id=obj_1')
    html = r.get_data(as_text=True)
    assert r.status_code == 200, html[:500]
    assert 'Program analysis' in html and 'Workouts at a glance' in html
    assert 'Add 2 more exercises for PULL-VERT' in html
    assert 'Data quality' in html and 'Mystery move' in html
    assert 'pa-chart-patterns' in html and 'Plotly.newPlot' in html
    assert 'program-analysis-dialog .pa-chart' in html
    assert 'width: calc(100% - 2rem)' in html and 'margin-inline: 1rem' in html
    assert 'pa-chart-objective' in html and 'pa-chart-laterality' in html


def test_ramp_toggle_changes_report(client):
    off = client.get('/program_analysis/report?program_id=prog1&objective_id=').get_data(as_text=True)
    on = client.get('/program_analysis/report?program_id=prog1&objective_id=&include_ramp=1').get_data(as_text=True)
    assert 'Jog' not in off.split('Repeated exercises')[0] or 'RAMP' not in off
    assert '>RAMP<' in on and '>RAMP<' not in off


def test_print_page_and_exports(client):
    html = client.get('/program_analysis/print?program_id=prog1&objective_id=builtin-balanced').get_data(as_text=True)
    assert '<!doctype html>' in html and 'window.print()' in html
    assert '.pa-chart { width: 100%; }' in html and 'program-analysis-dialog' not in html
    xlsx = client.get('/program_analysis/export?program_id=prog1&format=xlsx&objective_id=builtin-balanced')
    assert xlsx.status_code == 200 and xlsx.data[:2] == b'PK' and '.xlsx' in xlsx.headers['Content-Disposition']
    assert client.get('/program_analysis/export?program_id=prog1&format=csv').data.startswith(b'workout,')
    assert client.get('/program_analysis/export?program_id=prog1&format=json').json['analysis']['totals']['exercises'] == 7
    assert client.get('/program_analysis/export?program_id=prog1&format=bogus').status_code == 400


def test_objective_pages_render(client, monkeypatch):
    from views.program_analysis import program_analysis_routes as routes
    monkeypatch.setattr(routes, '_can_manage', lambda m: True)
    monkeypatch.setattr(routes, '_can_edit', lambda m, o: True)
    assert 'Upper focus' in client.get('/program_analysis/objectives').get_data(as_text=True)
    edit = client.get('/program_analysis/objectives/edit?id=obj_1').get_data(as_text=True)
    assert 'PULL-VERT' in edit and 'paSerializeRules' in edit
    assert 'New objective' in client.get('/program_analysis/objectives').get_data(as_text=True)


def test_workout_report_controls_and_exports(client):
    report = client.get('/program_analysis/report?workout_id=w1&objective_id=obj_1')
    html = report.get_data(as_text=True)
    assert report.status_code == 200
    assert 'Workout analysis' in html and 'Day A' in html and 'Day B' not in html
    assert 'name="workout_id" value="w1"' in html
    assert 'Apply to program' not in html
    assert 'workout_id=w1' in html and 'objective_id=obj_1' in html
    assert 'Not covered anywhere in the workout' in html
    assert 'Workout at a glance' in html
    on = client.get('/program_analysis/export?workout_id=w1&include_ramp=1&format=json').json
    off = client.get('/program_analysis/export?workout_id=w1&format=json').json
    assert off['analysis']['totals']['exercises'] == 3
    assert on['analysis']['totals']['exercises'] == 4
    assert len(on['analysis']['workouts']) == 1
    xlsx = client.get('/program_analysis/export?workout_id=w1&format=xlsx')
    assert xlsx.data[:2] == b'PK'
    from openpyxl import load_workbook
    workbook = load_workbook(BytesIO(xlsx.data), read_only=True)
    assert workbook['Gaps']['D1'].value == 'Missing from whole workout'
    assert b'Day A' in client.get('/program_analysis/export?workout_id=w1&format=csv').data
    printed = client.get('/program_analysis/print?workout_id=w1').get_data(as_text=True)
    assert 'Workout analysis' in printed and 'Day A' in printed


def test_workout_listing_key_and_access_control(client, monkeypatch):
    from views.program_analysis import program_analysis_routes as routes
    url = "/program_analysis/report?scope=workout&key=%5B%27w1%27%2C%20%27workout%27%5D"
    assert client.get(url).status_code == 200
    assert client.get('/program_analysis/report?workout_id=missing').status_code == 404
    assert client.get('/program_analysis/report?scope=workout&key=invalid').status_code == 400
    assert client.get('/program_analysis/report?program_id=prog1&workout_id=w1').status_code == 400
    monkeypatch.setattr(routes, 'filter_entities_by_member_role', lambda member_id, entities: [])
    for path in ('report', 'print', 'export'):
        assert client.get(f'/program_analysis/{path}?workout_id=w1').status_code == 403


def test_workout_builder_button_uses_saved_definition(client):
    app = client.app
    app.jinja_env.globals['url_for'] = lambda endpoint, **kwargs: (
        '/program_analysis/report?workout_id=' + kwargs['workout_id']
        if endpoint == 'program_analysis.report' else '/other'
    )
    with app.app_context():
        template = app.jinja_env.get_template('workouts/workout_builder2.html')
        args = dict(workout=WORKOUTS[0], workout_type='workout_definition',
                    role_context={'role': 'client'}, can_save_workout=True,
                    can_delete_workout=True, editing_program_workout=False)
        saved = template.render(**args, can_analyze_workout=True)
        assert 'hx-get="/program_analysis/report?workout_id=w1"' in saved
        assert 'Analyze the last saved workout' in saved
        draft = template.render(**args, can_analyze_workout=False)
        assert 'disabled title="Save the workout before analyzing it"' in draft
        args['workout_type'] = 'workout_instance'
        assert 'Analyze the last saved workout' not in template.render(**args, can_analyze_workout=False)


def test_workout_listing_actions_in_list_and_card(client, monkeypatch):
    from jinja2 import ChoiceLoader, FileSystemLoader
    from views.workouts import workout_routes

    app = client.app
    app.jinja_loader = ChoiceLoader([app.jinja_loader, FileSystemLoader(os.path.join(ROOT, 'common', 'templates'))])
    app.jinja_env.globals['url_for'] = lambda endpoint, **kwargs: (
        '/program_analysis/report?scope=workout' if endpoint == 'program_analysis.report' else '/other'
    )
    monkeypatch.setattr(workout_routes, 'url_for', app.jinja_env.globals['url_for'])
    monkeypatch.setattr(workout_routes, 'hx_render_template',
                        lambda template, **kwargs: flask.render_template('entity_results_partial.html', **kwargs))
    entity = {'key': ('w1', 'workout'), 'entity_id': 'w1', 'is_favorite': False,
              'field_values': ['Day A'], 'card_view_fields': {'title': 'Day A'}}
    with app.test_request_context('/workouts/workouts-listing'):
        for view in ('list', 'card'):
            html = workout_routes.workouts_listing_base(
                {}, 'MemberWorkoutDefinitionTable', 1, None, view, {'listing_view': ['Name']},
                [], [entity])
            assert 'Analyze Workout' in html and '/program_analysis/report?scope=workout' in html
            assert 'hx-target="#modals-here"' in html
            multi = workout_routes.workouts_listing_base(
                {}, 'MemberWorkoutDefinitionTable', 1, None, view, {'listing_view': ['Name']},
                [], [entity], allow_multi_select=True)
            assert 'Analyze Workout' not in multi
