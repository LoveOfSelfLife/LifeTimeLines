import inspect
import json
import copy
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest
from flask import Flask, render_template
from werkzeug.datastructures import MultiDict
from werkzeug.exceptions import BadRequest, NotFound


SERVICE = Path(__file__).resolve().parents[2] / 'services' / 'fitnessclub'


@pytest.fixture
def active_workout(monkeypatch):
    monkeypatch.syspath_prepend(str(SERVICE))
    from views.workouts import workout_routes as routes

    instance_key = ('workout', 'member', 'MemberWorkoutInstanceTable')
    workout = {'workout_sections': [{'name': 'Strength & Core', 'exercises': [
        {'id': 'primary', 'parameters': {'R': 5}, 'alternatives': [
            {'id': 'old', 'parameters': {'R': 8}}]},
    ]}]}
    exercises = {key: {'id': key, 'name': key.title()} for key in ('primary', 'old', 'new', 'other')}
    saved = []
    cleared = []
    state = {}

    class Store:
        def get_item_by_composite_key(self, key):
            if tuple(key) == instance_key:
                return workout
            if key[2] == 'ExerciseTable':
                return exercises.get(key[0])

        def upsert_item(self, item):
            saved.append(item)

    monkeypatch.setattr(routes, 'EntityStore', Store)
    monkeypatch.setattr(routes, 'get_entity', lambda table, key: exercises.get(key))
    monkeypatch.setattr(routes, 'get_member_id_from_user_context', lambda context: 'member')
    monkeypatch.setattr(routes, 'clear_selected_entity_keys', cleared.append)
    monkeypatch.setattr(routes, 'get_active_workout_state', lambda: state)
    monkeypatch.setattr(routes, 'update_active_workout_state', lambda value: state.update(value))
    app = Flask(__name__, template_folder=str(SERVICE / 'templates'))
    app.register_blueprint(routes.bp, url_prefix='/workouts')
    app.add_url_rule('/exercises/listing-modal', 'exercises.exercises_listing_modal', lambda: '')
    app.secret_key = 'test'
    key = str(instance_key)

    def call(view, method='GET', form=None, query=None, slot=0):
        with app.test_request_context('/', method=method, data=form, query_string=query):
            return inspect.unwrap(view)(context={}, section_name='Strength & Core', slot_index=slot)

    return routes, workout, exercises, saved, cleared, app, key, call


def test_choice_routes_preserve_special_characters(active_workout):
    routes, _, _, _, _, _, key, call = active_workout
    html = call(routes.choose_active_exercise_addition, query={'workout_instance_key': key})
    from html.parser import HTMLParser

    class Parser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.urls = []

        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if tag == 'button' and 'hx-get' in attrs:
                self.urls.append(attrs['hx-get'])

    parser = Parser()
    parser.feed(html)
    assert len(parser.urls) == 2
    for url, expected in zip(parser.urls, ('/active/add', '/alternatives/Strength%20%26%20Core/0/add')):
        post_url = parse_qs(urlparse(url).query)['multi_select_post_route'][0]
        assert expected in post_url
        assert parse_qs(urlparse(post_url).query)['workout_instance_key'] == [key]
    assert parse_qs(urlparse(parse_qs(urlparse(parser.urls[0]).query)['multi_select_post_route'][0]).query)['section_name'] == ['Strength & Core']


def test_add_alternatives_returns_updated_modal_and_refreshes(active_workout):
    routes, workout, _, saved, cleared, _, key, call = active_workout
    selection = MultiDict([('selected_entity_keys', str((name, 'all', 'ExerciseTable')))
                           for name in ('new', 'other', 'new', 'primary', 'old')])
    response = call(routes.add_active_alternatives, 'POST', selection, {'workout_instance_key': key})
    item = workout['workout_sections'][0]['exercises'][0]
    assert [alt['id'] for alt in item['alternatives']] == ['old', 'new', 'other']
    assert item['alternatives'][1]['parameters'] == routes.get_initial_params_for_exercise()
    assert len(saved) == 1 and cleared == ['member']
    assert 'New' in response.get_data(as_text=True) and 'Other' in response.get_data(as_text=True)
    assert 'workoutChanged' in json.loads(response.headers['HX-Trigger'])


def test_no_selection_or_invalid_selection_does_not_change_workout(active_workout):
    routes, workout, _, saved, _, _, key, call = active_workout
    response = call(routes.add_active_alternatives, 'POST', query={'workout_instance_key': key})
    assert response.status_code == 204
    with pytest.raises(BadRequest):
        call(routes.add_active_alternatives, 'POST', {'selected_entity_keys': 'invalid'}, {'workout_instance_key': key})
    with pytest.raises(NotFound):
        call(routes.add_active_alternatives, 'POST',
             {'selected_entity_keys': str(('missing', 'all', 'ExerciseTable'))}, {'workout_instance_key': key})
    with pytest.raises(BadRequest):
        call(routes.add_active_alternatives, 'POST', query={'workout_instance_key': 'invalid'})
    assert not saved
    assert [alt['id'] for alt in workout['workout_sections'][0]['exercises'][0]['alternatives']] == ['old']


def test_remove_alternative_refreshes_modal_and_reports_missing(active_workout):
    routes, workout, _, saved, _, _, key, call = active_workout
    data = {'workout_instance_key': key, 'alternative_exercise_id': 'old'}
    response = call(routes.remove_active_alternative, 'POST', data)
    assert workout['workout_sections'][0]['exercises'][0]['alternatives'] == []
    assert 'No alternative exercises available' in response.get_data(as_text=True)
    assert 'workoutChanged' in json.loads(response.headers['HX-Trigger'])
    assert len(saved) == 1
    with pytest.raises(NotFound):
        call(routes.remove_active_alternative, 'POST', data)


def test_alternatives_modal_has_swap_and_confirmed_delete(active_workout):
    routes, _, _, _, _, _, key, call = active_workout
    html = call(routes.show_exercise_alternatives, query={'workout_instance_key': key})
    assert 'Use this' in html and 'bi-trash' in html
    assert 'hx-confirm="Remove this alternative exercise?"' in html


def test_new_alternative_can_be_swapped_and_old_primary_preserved(active_workout):
    routes, workout, _, _, _, _, key, call = active_workout
    call(routes.add_active_alternatives, 'POST',
         {'selected_entity_keys': str(('new', 'exercise', 'ExerciseTable'))}, {'workout_instance_key': key})
    response = call(routes.swap_exercise_alternative, 'POST',
                    {'workout_instance_key': key, 'alternative_exercise_id': 'new'})
    item = workout['workout_sections'][0]['exercises'][0]
    assert item['id'] == 'new'
    assert [alt['id'] for alt in item['alternatives']] == ['old', 'primary']
    assert item['alternatives'][1]['parameters'] == {'R': 5}
    assert set(json.loads(response.headers['HX-Trigger'])) == {'exerciseSwapped', 'closeModal'}


@pytest.mark.parametrize('template', ['_section_dynamic_view.html', '_section_dynamic_carousel_view.html'])
@pytest.mark.parametrize('allow_edit', [True, False])
def test_both_layouts_expose_choice_and_existing_controls(active_workout, template, allow_edit):
    _, workout, exercises, _, _, app, key, _ = active_workout
    app.jinja_env.globals['rs'] = lambda value: value.replace(' ', '')
    with app.test_request_context('/'):
        html = render_template(
            'workouts/' + template, section=workout['workout_sections'][0], exercises=exercises,
            workout={'id': 'workout'}, active_workout=True, workout_instance_key=key,
            allow_on_the_fly_workout=allow_edit, default_exercise_index=None,
            exercise_parameters={'primary': {'param_list': []}})
    assert 'bi-clock-history' in html and 'bi-arrow-left-right' in html
    assert ('Add exercises or alternatives' in html) == allow_edit
    assert ('Remove this exercise' in html) == allow_edit
    workout['workout_sections'][0]['exercises'][0]['alternatives'] = []
    with app.test_request_context('/'):
        html = render_template(
            'workouts/' + template, section=workout['workout_sections'][0], exercises=exercises,
            workout={'id': 'workout'}, active_workout=True, workout_instance_key=key,
            allow_on_the_fly_workout=allow_edit, default_exercise_index=None,
            exercise_parameters={'primary': {'param_list': []}})
    assert 'bi-arrow-left-right' not in html


def test_alternative_changes_follow_swaps_and_slot_shifts():
    from common.fitness.exercise_alternatives import perform_exercise_swap, record_exercise_swap
    from common.fitness.exercise_onthefly import (
        apply_recorded_alternative_changes, record_alternative_changes, shift_alternative_changes,
    )

    original = {'id': 'primary', 'parameters': {'R': 5},
                'alternatives': [{'id': 'old', 'parameters': {'R': 8}}]}
    item = copy.deepcopy(original)
    state = {}
    item['alternatives'].append({'id': 'new', 'parameters': {'R': 10}})
    record_alternative_changes(state, 'Strength', 0, item)
    swap = perform_exercise_swap(item, 'new')
    record_exercise_swap(state, 'Strength', 0, swap)
    record_alternative_changes(state, 'Strength', 0, item)
    shift_alternative_changes(state, 'Strength', -1, inserted=True)

    definition = {'workout_sections': [{'name': 'Strength', 'exercises': [
        {'id': 'inserted', 'parameters': {}, 'alternatives': []}, copy.deepcopy(original)]}]}
    apply_recorded_alternative_changes(definition, state['alternative_changes'])
    assert definition['workout_sections'][0]['exercises'][1] == item
    shift_alternative_changes(state, 'Strength', 0, inserted=False)
    assert state['alternative_changes'][0]['slot_index'] == 0
    shift_alternative_changes(state, 'Strength', 0, inserted=False)
    assert state['alternative_changes'] == []


def test_changes_after_a_previously_swapped_slot_moves():
    from common.fitness.exercise_alternatives import perform_exercise_swap, record_exercise_swap
    from common.fitness.exercise_onthefly import record_alternative_changes, apply_recorded_alternative_changes

    original = {'id': 'primary', 'parameters': {'R': 5},
                'alternatives': [{'id': 'old', 'parameters': {'R': 8}}]}
    item = copy.deepcopy(original)
    state = {}
    record_exercise_swap(state, 'Strength', 0, perform_exercise_swap(item, 'old'))
    item['alternatives'].append({'id': 'new', 'parameters': {}})
    record_alternative_changes(state, 'Strength', 1, item)
    definition = {'workout_sections': [{'name': 'Strength', 'exercises': [
        {'id': 'inserted', 'parameters': {}}, copy.deepcopy(original)]}]}
    apply_recorded_alternative_changes(definition, state['alternative_changes'])
    assert definition['workout_sections'][0]['exercises'][1] == item


@pytest.mark.parametrize('strategy', ['original', 'performed_today'])
def test_finish_workout_respects_next_time_strategy(active_workout, monkeypatch, strategy):
    _, _, _, _, _, app, _, _ = active_workout
    from views.program import programs_routes as routes
    from common.fitness.exercise_onthefly import record_alternative_changes

    original = {'id': 'primary', 'parameters': {'R': 5},
                'alternatives': [{'id': 'old', 'parameters': {'R': 8}}]}
    item = copy.deepcopy(original)
    item['alternatives'].append({'id': 'new', 'parameters': {'R': 10}})
    definition = {'workout_sections': [{'name': 'Strength', 'exercises': [copy.deepcopy(original)]}]}
    instance = {'id': 'workout', 'member_id': 'member', 'member_workout_def_id': 'definition',
                'workout_sections': [{'name': 'Strength', 'exercises': [item]}]}
    state = {'adjustments': {}}
    record_alternative_changes(state, 'Strength', 0, item)
    saved = []

    class Store:
        def get_item_by_composite_key(self, key):
            return instance

        def get_item(self, key):
            return definition

        def upsert_item(self, obj):
            saved.append(obj)

    monkeypatch.setattr(routes, 'EntityStore', Store)
    monkeypatch.setattr(routes, 'get_active_workout_state', lambda: state)
    monkeypatch.setattr(routes, 'get_exercise_parameters', lambda member_id: {})
    monkeypatch.setattr(routes, 'on_workout_instance_saved', lambda obj: None)
    monkeypatch.setattr(routes, 'clear_active_workout_state', lambda member_id: None)
    monkeypatch.setattr(routes, 'clear_last_section', lambda member_id, workout_id: None)
    with app.test_request_context('/', method='POST', data={'next_time_strategy': strategy}):
        response = inspect.unwrap(routes.really_finish_workout)(
            context={}, workout_instance_key=str(('workout', 'member', 'MemberWorkoutInstanceTable')))
    assert response.status_code == 302
    if strategy == 'original':
        assert definition['workout_sections'][0]['exercises'][0] == original
        assert len(saved) == 1
    else:
        assert definition['workout_sections'][0]['exercises'][0] == item
        assert len(saved) == 2
