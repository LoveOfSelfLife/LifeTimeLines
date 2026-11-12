import json

import pytest

from common.fitness.program_analysis import analyze as an
from common.fitness.program_analysis import charts, export, extract
from common.fitness.program_analysis import objectives as obj

EXERCISES = {
    'bench': {'name': 'Bench press', 'primaryMuscles': ['chest'], 'secondaryMuscles': ['triceps', 'shoulders'],
              'physical_fitness_components': ['strength'], 'movement_categories': ['PUSH-HORZ'], 'family': 'Press',
              'equipment_list': ['barbell']},
    'row': {'name': 'Row', 'primaryMuscles': ['middle_back', 'lats'], 'secondaryMuscles': ['biceps'],
            'physical_fitness_components': ['strength'], 'movement_categories': ['PULL-HORZ']},
    'shoulder_mob': {'name': 'Shoulder CARs', 'primaryMuscles': ['shoulders'],
                     'physical_fitness_components': ['mobility'], 'movement_categories': ['PUSH-VERT']},
    'split_squat': {'name': 'Split squat', 'primaryMuscles': ['quadriceps', 'glutes'],
                    'physical_fitness_components': ['strength', 'balance'], 'movement_categories': ['SQUAT-ASYM'],
                    'is_unilateral': True, 'is_alternating': True},
    'bike': {'name': 'Bike', 'primaryMuscles': ['quadriceps'], 'physical_fitness_components': ['cardio'],
             'movement_categories': []},
    'jog': {'name': 'Jog', 'primaryMuscles': ['calves'], 'physical_fitness_components': ['cardio'],
            'movement_categories': ['RAMP']},
    'bare': {'name': 'Mystery move'},
}


def item(i, **params):
    return {'id': i, 'parameters': params}


WORKOUTS = [
    {'id': 'w1', 'name': 'Day A', 'workout_sections': [
        {'name': 'ramp', 'exercises': [item('jog', S=1, T=5, Tu='min')]},
        {'name': 'strength', 'exercises': [item('bench', S=3, R=8), item('shoulder_mob', S=2, R=10),
                                           item('bare', S=1)]}]},
    {'id': 'w2', 'name': 'Day B', 'workout_sections': [
        {'name': 'strength', 'exercises': [item('row', S=4, R=8), item('split_squat', S=3, R=8),
                                           item('bench', S=2, R=10)]},
        {'name': 'cardio', 'exercises': [item('bike', S=1, T=20, Tu='min')]}]},
]


def run(include_ramp=False, workouts=WORKOUTS):
    infos, rows = extract.flatten_program(workouts, EXERCISES)
    return infos, rows, an.analyze(infos, rows, include_ramp=include_ramp)


def test_ramp_toggle():
    _, _, off = run(False)
    _, _, on = run(True)
    assert off['totals']['exercises'] == 7 and on['totals']['exercises'] == 8
    assert 'RAMP' not in off['tables']['parent_pattern']
    assert on['tables']['parent_pattern']['RAMP']['total_exercises'] == 1


def test_load_workout_rows_resolves_only_referenced_exercises(monkeypatch):
    from common import entity_store

    calls = []

    class Store:
        def get_item(self, entity):
            calls.append(entity['id'])
            return EXERCISES.get(entity['id'])

    monkeypatch.setattr(entity_store, 'EntityStore', Store)
    infos, rows = extract.load_workout_rows([WORKOUTS[0]])
    assert infos[0]['name'] == 'Day A'
    assert {row['exercise_id'] for row in rows} == {'jog', 'bench', 'shoulder_mob', 'bare'}
    assert set(calls) == {'jog', 'bench', 'shoulder_mob', 'bare'}


def test_mobility_does_not_count_as_shoulder_strength():
    _, _, a = run()
    strength = a['tables']['muscle']['strength']['shoulders']
    # only the bench press (secondary, weight 0.5) strengthens the shoulders: (3 + 2 sets) * 0.5
    assert strength['total_sets'] == pytest.approx(2.5)
    assert a['tables']['muscle']['mobility']['shoulders']['total_sets'] == pytest.approx(2)


def test_secondary_weight_is_configurable():
    infos, rows = extract.flatten_program(WORKOUTS, EXERCISES)
    a = an.analyze(infos, rows, secondary_weight=0.25)
    assert a['tables']['muscle']['strength']['triceps']['total_exercises'] == pytest.approx(0.5)


def test_multi_pfc_gives_full_credit_to_each_bucket():
    _, _, a = run()
    assert a['tables']['pfc']['balance']['total_exercises'] == 1
    assert a['tables']['pfc']['strength']['total_exercises'] == 4
    # strength+balance maps to strength and other: glutes credited in the strength bucket and the other bucket
    assert a['tables']['muscle']['strength']['glutes']['total_sets'] == 3
    assert a['tables']['muscle']['other']['glutes']['total_sets'] == 3


def test_laterality_and_cardio():
    _, _, a = run()
    assert a['tables']['laterality']['alternating']['total_exercises'] == 1
    assert a['tables']['laterality']['bilateral']['total_exercises'] == 6
    assert a['cardio']['exercises'] == 1 and a['cardio']['minutes'] == 20


def test_gaps_and_uncovered():
    _, _, a = run()
    day_a = a['gaps'][0]
    pattern_gaps = {g['key']: g['program_wide'] for g in day_a['pattern']}
    assert pattern_gaps['SQUAT-ASYM'] is False       # day B covers it
    assert pattern_gaps['HINGE-BRIDGE'] is True      # nobody covers it
    assert 'PULL-HORZ' in a['uncovered']['pattern'] or a['tables']['pattern']['PULL-HORZ']['total_exercises'] == 1
    assert 'neck' in a['uncovered']['muscle'] and 'chest' not in a['uncovered']['muscle']


def test_repeats():
    _, _, a = run()
    assert a['repeats']['exercises'][0]['name'] == 'Bench press'
    assert a['repeats']['exercises'][0]['workouts'] == ['Day A', 'Day B']


def test_data_quality_flags_missing_attributes_and_assumed_sets():
    _, _, a = run()
    names = {m['name']: m['missing'] for m in a['data_quality']['missing_attributes']}
    assert set(names['Mystery move']) == {'movement category', 'fitness component', 'primary muscle'}
    assert names['Bike'] == ['movement category']
    assert any(m['name'] == 'Shoulder CARs' for m in a['data_quality']['assumed_sets']) is False
    assert any(m['name'] == 'Mystery move' for m in a['data_quality']['assumed_sets']) is False  # S=1 given


def test_missing_exercise_is_flagged():
    infos, rows = extract.flatten_program([{'id': 'w', 'name': 'W', 'workout_sections': [
        {'name': 's', 'exercises': [item('gone', S=2)]}]}], {})
    a = an.analyze(infos, rows)
    assert a['data_quality']['missing_attributes'][0]['missing'] == ['exercise definition']


def test_essence_text():
    _, _, a = run()
    assert 'PUSH-HORZ ×1' in a['essence'][0]['text']
    assert a['essence'][1]['unilateral_pct'] == 25


def test_objective_count_pct_and_max():
    _, _, a = run()
    objective = {'name': 'Custom', 'rules': [
        {'dimension': 'pattern', 'key': 'PULL-VERT', 'min': 2},
        {'dimension': 'parent_pattern', 'key': 'PUSH', 'target': 30, 'tolerance': 5},
        {'dimension': 'pattern', 'key': 'SQUAT-ASYM', 'max': 0},
        {'dimension': 'muscle', 'keys': ['chest', 'neck'], 'min': 1},
    ]}
    ev = obj.evaluate(a, objective)
    by_key = {(r['key'], r['status']): r for r in ev['results']}
    assert ('PULL-VERT', 'under') in by_key and 'Add 2' in by_key[('PULL-VERT', 'under')]['suggestion']
    assert ('SQUAT-ASYM', 'over') in by_key
    assert ('chest', 'met') in by_key and ('neck', 'under') in by_key
    push = next(r for r in ev['results'] if r['key'] == 'PUSH')
    assert push['metric'] == 'pct_sets' and push['status'] in ('under', 'over', 'met')
    assert ev['met'] == sum(1 for r in ev['results'] if r['status'] == 'met')


def test_balanced_builtin_expands_all_keys():
    _, _, a = run()
    ev = obj.evaluate(a, obj.balanced_objective())
    assert ev['total'] > 40 and ev['met'] < ev['total']


def test_validate_rules():
    assert obj.validate_rules([]) 
    assert obj.validate_rules([{'dimension': 'nope', 'key': 'x', 'min': 1}])
    assert obj.validate_rules([{'dimension': 'muscle', 'key': 'chest'}])
    assert not obj.validate_rules([{'dimension': 'muscle', 'key': 'chest', 'min': 1}])


def test_charts_and_exports():
    infos, rows, a = run()
    ev = obj.evaluate(a, obj.balanced_objective())
    figs = charts.build_charts(a, ev)
    assert {'patterns', 'muscles', 'pfc', 'laterality', 'objective', 'pattern_heatmap'} <= set(figs)
    assert all('data' in json.loads(f) for f in figs.values())
    sheet_map = export.sheets(a, infos, rows, ev)
    assert 'Exercises' in sheet_map and 'Objective' in sheet_map
    assert export.to_xlsx(sheet_map)[:2] == b'PK'
    assert export.to_csv(infos, rows).count('\n') >= len(rows)
    assert json.loads(export.to_json(a, ev))['analysis']['totals']['exercises'] == 7


def test_empty_program():
    infos, rows = extract.flatten_program([], {})
    a = an.analyze(infos, rows)
    assert a['totals']['exercises'] == 0 and charts.build_charts(a) == {}
