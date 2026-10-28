import json

from common.fitness.exercise_history_analytics import (
    LBS_TO_KG, aggregate_over_time, build_chart_json, build_history_dataframe,
    compute_event_metrics, group_events, summarize_groups)


def _event(date, ex, workout, **params):
    return {'date_time': date, 'exercise_id': ex, 'member_workout_instance_id': workout, **params}


def test_metrics_kinds_and_unit_conversion():
    load = compute_event_metrics({'sets': '3', 'reps': '10', 'weight': '100', 'weight_unit': 'lbs'})
    assert load['volume_kind'] == 'load'
    assert abs(load['volume'] - 30 * 100 * LBS_TO_KG) < 1e-6
    assert compute_event_metrics({'sets': 3, 'reps': 10})['volume_kind'] == 'reps'
    assert compute_event_metrics({'sets': 2, 'time': 30})['volume'] == 60
    band = compute_event_metrics({'sets': 3, 'reps': 10, 'weight': 'red', 'weight_unit': 'band'})
    assert band['volume_kind'] == 'reps' and band['volume'] == 30


def _df():
    exercises = {
        'pu': {'name': 'Push-up', 'family': 'Push-up', 'movement_categories': ['PUSH-HORZ']},
        'dpu': {'name': 'Decline push-up', 'family': 'Push-up', 'movement_categories': ['PUSH-HORZ', 'PUSH-VERT']},
        'bp': {'name': 'Bench press', 'movement_categories': ['PUSH-HORZ']},
    }
    events = [
        _event('2025-01-06T10:00:00Z', 'pu', 'w1', sets=3, reps=10),
        _event('2025-01-08T10:00:00Z', 'dpu', 'w2', sets=3, reps=8),
        _event('2025-01-09T10:00:00Z', 'bp', 'w2', sets=3, reps=5, weight=50, weight_unit='kg'),
        _event('2025-02-03T10:00:00Z', 'pu', 'w3', sets=2, reps=10),
    ]
    return build_history_dataframe(events, exercises)


def test_grouping_counts_event_in_each_group():
    df = _df()
    fam = {g['group']: g for g in summarize_groups(df, 'family')}
    assert set(fam) == {'Push-up', 'Bench press'}
    assert fam['Push-up']['exercise_count'] == 2
    mov = {g['group']: g for g in summarize_groups(df, 'movement')}
    assert mov['PUSH-HORZ']['exercise_count'] == 3
    assert mov['PUSH-VERT']['workout_count'] == 1


def test_aggregation_and_chart():
    df = group_events(_df(), 'family', 'Push-up')
    per_workout = aggregate_over_time(df, 'volume', 'workout')
    assert len(per_workout) == 3
    monthly = aggregate_over_time(df, 'reps', 'month')
    assert list(monthly['value']) == [54, 20]
    weekly = aggregate_over_time(df, 'sets', 'week')
    assert weekly['value'].sum() == 8
    chart = json.loads(build_chart_json(df, 'volume', 'month'))
    assert chart['data']
    assert build_chart_json(df.iloc[0:0]) is None
