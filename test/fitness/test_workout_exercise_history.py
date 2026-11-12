import inspect
from pathlib import Path

import pytest
from flask import Flask, render_template
from werkzeug.exceptions import BadRequest, Forbidden, NotFound

from common.fitness import exercise_analytics_db as db


SERVICE = Path(__file__).resolve().parents[2] / 'services' / 'fitnessclub'


@pytest.fixture
def history_view(monkeypatch, tmp_path):
    monkeypatch.syspath_prepend(str(SERVICE))
    from views.workouts import workout_routes as routes

    workout = {
        'id': 'current',
        'assigned_to_member_id': 'member',
        'workout_sections': [{'name': 'main', 'section_type': 'strength',
                              'exercises': [{'id': 'bench', 'parameters': {}, 'alternatives': []}]}],
    }
    state = {'current_workout': workout, 'workout_type': 'MemberWorkoutDefinitionTable'}
    viewer = {'id': 'coach', 'role': 'coach', 'accessible': ['member']}
    exercises = {'bench': {'id': 'bench', 'name': 'Bench press', 'setCompletionMeasure': 'reps'}}
    db_path = str(tmp_path / 'history.sqlite')
    real_connect = db.connect
    conn = real_connect(db_path)
    for wid, member, date, parameters in [
        ('old', 'member', '2025-01-01', {'S': 3, 'R': 5, 'F': 100, 'Fu': 'lbs'}),
        ('new', 'member', '2025-02-01', {'S': 2, 'R': 8, 'F': 50, 'Fu': 'kg', 'T': 2, 'Tu': 'min'}),
        ('other', 'other', '2025-03-01', {'S': 9, 'R': 99}),
        ('current', 'member', '2025-04-01', {'S': 7, 'R': 77}),
    ]:
        db.upsert_workout_instance(conn, {
            'id': wid, 'member_id': member, 'name': wid,
            'started_ts': date + 'T10:00:00Z', 'finished_ts': date + 'T11:00:00Z',
            'workout_sections': [{'name': 'main', 'exercises': [{'id': 'bench', 'parameters': parameters}]}],
        }, exercises)
    conn.close()
    builds = []
    monkeypatch.setattr(routes, 'get_cache_value', state.get)
    monkeypatch.setattr(routes, 'get_member_id_from_user_context', lambda context: viewer['id'])
    monkeypatch.setattr(routes, 'is_member_an_admin', lambda member_id: viewer['role'] == 'admin')
    monkeypatch.setattr(routes, 'get_member_role_context', lambda member_id: {'role': viewer['role']})
    monkeypatch.setattr(routes, 'get_accessible_members_for_context',
                        lambda member_id: [{'id': mid} for mid in viewer['accessible']])
    monkeypatch.setattr(routes, 'get_user_profile',
                        lambda member_id: {'name': {'member': 'Alex Member', 'other': 'Taylor Other'}.get(member_id)})
    monkeypatch.setattr(routes, 'get_entity', lambda table, key: exercises.get(key))
    monkeypatch.setattr(routes, 'url_for', lambda endpoint, **kwargs: (
        '/workouts/viewer/current/exercise-history' if endpoint == 'workouts.active_workout_exercise_history'
        else '/workouts/builder/current/exercise-history'))
    monkeypatch.setattr(db, 'connect', lambda: real_connect(db_path))
    monkeypatch.setattr(db, 'ensure_member_built', lambda conn, member_id: builds.append(member_id))
    def render_history(template, **kwargs):
        kwargs['member_id'] = viewer['id']
        return render_template(template, **kwargs)

    monkeypatch.setattr(routes, 'hx_render_template', render_history)

    app = Flask(__name__, template_folder=str(SERVICE / 'templates'))
    app.jinja_env.globals['url_for'] = lambda endpoint, **kwargs: '/workouts/builder/current/exercise-history'
    view = inspect.unwrap(routes.workout_exercise_history)

    def request(query='?exercise_id=bench', workout_id='current'):
        with app.test_request_context('/workouts/builder/current/exercise-history' + query):
            return view(context={}, workout_id=workout_id)

    return request, state, viewer, builds, app, exercises


def test_assigned_member_history_and_units(history_view):
    request, state, viewer, builds, _, _ = history_view
    state['workout_type'] = 'MemberWorkoutInstanceTable'
    html = request()
    assert builds == ['member']
    assert 'Bench press History' in html
    assert '<strong>Member:</strong> Alex Member' in html
    assert html.index('2025-02-01') < html.index('2025-01-01')
    assert '2025-03-01' not in html and '2025-04-01' not in html
    assert '<td>110.23</td>' in html and '<td>100</td>' in html
    assert '<td>120</td>' in html and 'Time (seconds)' in html
    assert 'Weight (lbs)' in html and 'hx-trigger="change"' in html
    assert 'name="exercise_id" value="bench"' in html and 'name="unit"' in html
    assert 'bi-caret-down-fill' in html and 'pointer-events: none' in html
    assert 'modal-dialog-centered modal-dialog-scrollable exercise-history-dialog' in html
    assert 'modal-fullscreen-sm-down' not in html and '--bs-modal-margin: 1rem' in html

    kg_html = request('?exercise_id=bench&unit=kg')
    assert 'Weight (kg)' in kg_html
    assert '<strong>Member:</strong> Alex Member' in kg_html
    assert '<td>50</td>' in kg_html and '<td>45.36</td>' in kg_html
    assert 'value="kg" selected' in kg_html


def test_history_access_and_input_validation(history_view):
    request, state, viewer, builds, _, _ = history_view
    viewer['accessible'] = []
    with pytest.raises(Forbidden):
        request()
    viewer['role'] = 'client'
    viewer['accessible'] = ['member']
    with pytest.raises(Forbidden):
        request()
    assert not builds
    viewer['id'] = 'member'
    assert '2025-02-01' in request()
    viewer['id'] = 'admin'
    viewer['role'] = 'admin'
    assert '2025-02-01' in request()
    with pytest.raises(NotFound):
        request(workout_id='different')
    with pytest.raises(NotFound):
        request('?exercise_id=other')
    with pytest.raises(BadRequest):
        request('?exercise_id=bench&unit=stone')
    with pytest.raises(BadRequest):
        request('')


def test_no_member_and_empty_timed_history(history_view):
    request, state, viewer, builds, _, exercises = history_view
    state['current_workout'].pop('assigned_to_member_id')
    assert 'Assign this workout to a member' in request()
    assert not builds
    state['current_workout']['member_id'] = 'member'
    state['current_workout']['workout_sections'][0]['exercises'][0]['id'] = 'plank'
    exercises['plank'] = {'id': 'plank', 'name': 'Plank', 'setCompletionMeasure': 'time'}
    html = request('?exercise_id=plank')
    assert 'No previous workouts found' in html
    assert '<strong>Member:</strong> Alex Member' in html
    assert builds == ['member']


def test_history_without_time_hides_time_column(history_view):
    request, state, viewer, builds, _, _ = history_view
    state['current_workout']['assigned_to_member_id'] = 'other'
    viewer['id'] = 'other'
    html = request()
    assert '2025-03-01' in html
    assert '<strong>Member:</strong> Taylor Other' in html
    assert '2025-02-01' not in html
    assert 'Time (seconds)' not in html


def test_unassigned_definition_uses_creator_history(history_view):
    request, state, viewer, builds, _, _ = history_view
    workout = state['current_workout']
    workout['assigned_to_member_id'] = ''
    workout['created_by'] = 'other'
    workout['member_id'] = 'member'
    viewer['id'] = 'other'
    html = request()
    assert builds == ['other']
    assert '<strong>Member:</strong> Taylor Other' in html
    assert '2025-03-01' in html and '2025-02-01' not in html
    assert '<strong>Member:</strong> Taylor Other' in request('?exercise_id=bench&unit=kg')


def test_explicit_assignment_and_instance_member_take_precedence(history_view):
    request, state, viewer, builds, _, _ = history_view
    workout = state['current_workout']
    workout['created_by'] = 'other'
    assert '<strong>Member:</strong> Alex Member' in request()
    workout['assigned_to_member_id'] = ''
    workout['member_id'] = 'member'
    state['workout_type'] = 'MemberWorkoutInstanceTable'
    assert '<strong>Member:</strong> Alex Member' in request()
    assert builds == ['member', 'member']


def test_creator_history_requires_access(history_view):
    request, state, viewer, builds, _, _ = history_view
    state['current_workout']['assigned_to_member_id'] = ''
    state['current_workout']['created_by'] = 'other'
    with pytest.raises(Forbidden):
        request()
    assert builds == []
    viewer['accessible'] = ['other']
    assert '<strong>Member:</strong> Taylor Other' in request()
    assert builds == ['other']


def test_missing_member_name_is_explicit(history_view, monkeypatch, caplog):
    request, _, _, _, _, _ = history_view
    from views.workouts import workout_routes as routes
    monkeypatch.setattr(routes, 'get_user_profile', lambda member_id: None)
    html = request()
    assert 'Name unavailable (member)' in html
    assert 'No name found for exercise history member' in caplog.text


def test_canvas_renders_history_action(history_view):
    _, state, _, _, app, exercises = history_view
    workout = state['current_workout']
    with app.test_request_context('/'):
        html = render_template('workouts/_workout_dynamic_canvas.html', workout=workout, exercises=exercises,
                               exercise_parameters={'main': {'bench': {'param_list': []}}},
                               workout_id='current', can_edit_parameters=True)
    assert 'workout-item-actions flex-wrap' in html
    assert 'bi-clock-history' in html and '>History</span>' in html
    assert '/workouts/builder/current/exercise-history' in html
    assert 'exercise_id' in html and 'bench' in html


@pytest.mark.parametrize('template', [
    'workouts/_section_dynamic_view.html',
    'workouts/_section_dynamic_carousel_view.html',
])
def test_active_workout_views_show_accessible_history_button(history_view, template):
    _, state, _, _, app, exercises = history_view
    app.jinja_env.globals['url_for'] = lambda endpoint, **kwargs: (
        '/workouts/viewer/current/exercise-history' if endpoint == 'workouts.active_workout_exercise_history'
        else '/other')
    workout = state['current_workout']
    args = dict(workout=workout, section=workout['workout_sections'][0], exercises=exercises,
                exercise_parameters={'bench': {'param_list': []}}, active_workout=True,
                workout_instance_key=['current', 'member', 'MemberWorkoutInstanceTable'],
                default_exercise_index=None, rs=lambda value: value)
    with app.test_request_context('/'):
        html = render_template(template, **args)
        assert 'aria-label="View history for Bench press"' in html
        assert 'bi-clock-history' in html and '/workouts/viewer/current/exercise-history' in html
        assert 'exercise_id' in html and 'bench' in html
        args['active_workout'] = False
        assert 'bi-clock-history' not in render_template(template, **args)


def test_active_history_uses_session_workout_and_member(history_view, monkeypatch):
    _, state, viewer, builds, app, exercises = history_view
    from views.workouts import workout_routes as routes
    viewer['id'] = 'member'
    workout = dict(state['current_workout'], member_id='member', assigned_to_member_id='other')
    active = {'state': 'workout_started',
              'workout_instance_key': ['current', 'member', 'MemberWorkoutInstanceTable']}
    monkeypatch.setattr(routes, 'get_active_workout_state', lambda: active)

    class Store:
        def get_item_by_composite_key(self, key):
            assert key == active['workout_instance_key']
            return workout

    monkeypatch.setattr(routes, 'EntityStore', Store)
    view = inspect.unwrap(routes.active_workout_exercise_history)

    def request(query='?exercise_id=bench', workout_id='current'):
        with app.test_request_context('/workouts/viewer/current/exercise-history' + query):
            return view(context={}, workout_id=workout_id)

    html = request()
    assert builds == ['member']
    assert '<strong>Member:</strong> Alex Member' in html
    assert '2025-02-01' in html and '2025-03-01' not in html and '2025-04-01' not in html
    assert 'hx-get="/workouts/viewer/current/exercise-history"' in html
    assert '<td>45.36</td>' in request('?exercise_id=bench&unit=kg')
    workout['workout_sections'] = [{'name': 'main', 'exercises': [{'id': 'plank'}]}]
    exercises['plank'] = {'id': 'plank', 'name': 'Plank', 'setCompletionMeasure': 'time'}
    assert 'No previous workouts found' in request('?exercise_id=plank')
    with pytest.raises(NotFound):
        request()
    with pytest.raises(NotFound):
        request(workout_id='another')
    with pytest.raises(NotFound):
        request('?exercise_id=missing')
    with pytest.raises(BadRequest):
        request('?exercise_id=plank&unit=stone')
    viewer['id'] = 'other'
    with pytest.raises(Forbidden):
        request()
    viewer['id'] = 'member'
    active['workout_instance_key'] = ['current', 'member', 'MemberWorkoutDefinitionTable']
    with pytest.raises(NotFound):
        request()
    active.clear()
    with pytest.raises(NotFound):
        request()
