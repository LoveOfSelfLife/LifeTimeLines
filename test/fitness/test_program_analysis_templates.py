"""Renders the program analysis templates through the real blueprint, with the entity store and auth stubbed out."""
import os
import sys

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
