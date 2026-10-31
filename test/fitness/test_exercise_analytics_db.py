import sqlite3

import pytest

from common.fitness import exercise_analytics_db as db
from common.fitness import exercise_analytics_queries as q

EXERCISES = {
    'pushup': {'name': 'Push-up', 'family': 'Push-up', 'primaryMuscles': ['chest', 'triceps'],
               'physical_fitness_components': ['strength', 'endurance'], 'movement_categories': ['PUSH-HORZ']},
    'bench': {'name': 'Bench press', 'primaryMuscles': ['chest'], 'physical_fitness_components': ['strength'],
              'movement_categories': ['PUSH-HORZ']},
    'squat': {'name': 'Squat', 'primaryMuscles': ['quadriceps'], 'physical_fitness_components': ['strength'],
              'movement_categories': ['SQUAT-SYM']},
    'plank': {'name': 'Plank', 'primaryMuscles': ['abdominals'], 'physical_fitness_components': ['core'],
              'movement_categories': ['CORE']},
}


def workout(wid, start, finish, items, member='m1'):
    return {'id': wid, 'member_id': member, 'name': 'W ' + wid, 'started_ts': start, 'finished_ts': finish,
            'workout_sections': [{'name': 'main', 'exercises': [{'id': i, 'parameters': p} for i, p in items]}]}


W1 = workout('w1', '2025-01-06T10:00:00Z', '2025-01-06T11:00:00Z', [
    ('pushup', {'sets': 3, 'reps': 10}),
    ('bench', {'sets': 3, 'reps': 5, 'weight': 100, 'weight_unit': 'lbs'}),
    ('squat', {'sets': 3, 'reps': 8, 'weight': 50, 'weight_unit': 'kg'}),
    ('plank', {'sets': 2, 'time': 30}),
])
W2 = workout('w2', '2025-01-13T10:00:00Z', '2025-01-13T11:00:00Z', [('pushup', {'sets': 2, 'reps': 12})])


@pytest.fixture
def conn():
    c = db.connect(':memory:')
    yield c
    c.close()


def count(conn, table):
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def test_q3_workout_exercises(conn):
    assert db.upsert_workout_instance(conn, W1, EXERCISES) == 4
    rows = q.workout_exercises(conn, 'w1')
    assert [r['name'] for r in rows] == ['Push-up', 'Bench press', 'Squat', 'Plank']
    assert rows[1]['weight_kg'] == pytest.approx(100 * db.LBS_TO_KG)
    assert rows[1]['volume_kg'] == pytest.approx(15 * 100 * db.LBS_TO_KG)


def test_idempotent(conn):
    db.upsert_workout_instance(conn, W1, EXERCISES)
    before = [tuple(r) for r in conn.execute("SELECT * FROM fact_exercise_performance ORDER BY fact_id")]
    db.upsert_workout_instance(conn, W1, EXERCISES)
    assert count(conn, 'fact_exercise_performance') == 4
    assert count(conn, 'dim_workout') == 1
    after = [tuple(r) for r in conn.execute("SELECT * FROM fact_exercise_performance ORDER BY fact_id")]
    assert [r[1:] for r in before] == [r[1:] for r in after]


def test_q1_exercise_history_and_edit(conn):
    db.upsert_workout_instance(conn, W1, EXERCISES)
    db.upsert_workout_instance(conn, W2, EXERCISES)
    rows = q.exercise_history(conn, 'm1', 'pushup')
    assert [r['performed_ts'][:10] for r in rows] == ['2025-01-13', '2025-01-06']
    assert rows[0]['reps'] == 12 and rows[0]['volume_kind'] == 'reps'

    # editing the workout replaces its facts, including when an exercise is removed
    edited = workout('w2', W2['started_ts'], W2['finished_ts'], [('pushup', {'sets': 4, 'reps': 12}),
                                                               ('squat', {'sets': 1, 'reps': 5})])
    db.upsert_workout_instance(conn, edited, EXERCISES)
    assert q.exercise_history(conn, 'm1', 'pushup')[0]['sets'] == 4
    assert len(q.workout_exercises(conn, 'w2')) == 2
    edited['workout_sections'][0]['exercises'].pop()
    db.upsert_workout_instance(conn, edited, EXERCISES)
    assert len(q.workout_exercises(conn, 'w2')) == 1


def test_duplicate_exercise_in_one_workout_keeps_both(conn):
    w = workout('w3', '2025-02-01T10:00:00Z', '2025-02-01T11:00:00Z',
                [('pushup', {'sets': 1, 'reps': 10}), ('pushup', {'sets': 1, 'reps': 20})])
    db.upsert_workout_instance(conn, w, EXERCISES)
    assert [r['reps'] for r in q.exercise_history(conn, 'm1', 'pushup')] == [10, 20]


def test_q2_muscle_history(conn):
    db.upsert_workout_instance(conn, W1, EXERCISES)
    db.upsert_workout_instance(conn, W2, EXERCISES)
    names = [r['name'] for r in q.muscle_history(conn, 'm1', 'chest')]
    assert sorted(names) == ['Bench press', 'Push-up', 'Push-up']
    assert q.muscle_history(conn, 'm2', 'chest') == []


def test_q4_muscles(conn):
    db.upsert_workout_instance(conn, W1, EXERCISES)
    m = {r['muscle']: r for r in q.workout_muscles(conn, 'w1')}
    assert m['chest']['exercise_count'] == 2 and m['chest']['total_sets'] == 6
    assert m['quadriceps']['exercise_count'] == 1 and m['quadriceps']['total_sets'] == 3
    assert m['triceps']['exercise_count'] == 1


def test_q5_fitness_components(conn):
    db.upsert_workout_instance(conn, W1, EXERCISES)
    c = {r['component']: r for r in q.workout_fitness_components(conn, 'w1')}
    # strength: bench 3 + squat 3 + half of pushup 1.5; endurance: half of pushup; core: plank 2
    assert c['strength']['allocated_sets'] == pytest.approx(7.5)
    assert c['endurance']['allocated_sets'] == pytest.approx(1.5)
    assert c['core']['allocated_sets'] == pytest.approx(2)
    assert sum(r['pct'] for r in c.values()) == pytest.approx(100, abs=0.2)


def test_q6_movements(conn):
    db.upsert_workout_instance(conn, W1, EXERCISES)
    m = {r['movement']: r for r in q.workout_movements(conn, 'w1')}
    assert m['PUSH']['allocated_sets'] == 6 and m['SQUAT']['allocated_sets'] == 3 and m['CORE']['allocated_sets'] == 2
    detailed = {r['movement'] for r in q.workout_movements(conn, 'w1', rollup=False)}
    assert 'PUSH-HORZ' in detailed and 'SQUAT-SYM' in detailed


def test_delete_workout(conn):
    db.upsert_workout_instance(conn, W1, EXERCISES)
    db.upsert_workout_instance(conn, W2, EXERCISES)
    assert db.delete_workout_instance(conn, 'w1') == 1
    assert q.workout_exercises(conn, 'w1') == []
    assert len(q.exercise_history(conn, 'm1', 'pushup')) == 1
    assert db.delete_workout_instance(conn, 'w1') == 0


def test_unfinished_workout_is_not_loaded(conn):
    unfinished = dict(W1, finished_ts=None)
    assert db.upsert_workout_instance(conn, unfinished, EXERCISES) == 0
    db.upsert_workout_instance(conn, W1, EXERCISES)
    db.upsert_workout_instance(conn, unfinished, EXERCISES)
    assert count(conn, 'fact_exercise_performance') == 0


def test_rebuild_member_removes_stale_and_other_members_untouched(conn):
    other = workout('o1', '2025-01-06T10:00:00Z', '2025-01-06T11:00:00Z', [('squat', {'sets': 1, 'reps': 1})], 'm2')
    db.upsert_workout_instance(conn, other, EXERCISES)
    db.upsert_workout_instance(conn, W1, EXERCISES)
    loaded, facts = db.rebuild_member(conn, 'm1', [W2], EXERCISES)
    assert (loaded, facts) == (1, 1)
    assert q.workout_exercises(conn, 'w1') == []
    assert len(q.workout_exercises(conn, 'o1')) == 1


def test_exercise_reclassification_applies_to_history(conn):
    db.upsert_workout_instance(conn, W2, EXERCISES)
    changed = dict(EXERCISES, pushup=dict(EXERCISES['pushup'], family='Press', primaryMuscles=['shoulders']))
    db.upsert_exercise(conn, 'pushup', changed['pushup'])
    assert q.muscle_history(conn, 'm1', 'chest') == []
    assert len(q.muscle_history(conn, 'm1', 'shoulders')) == 1
    assert q.family_trend(conn, 'm1', 'Press')[0]['total_reps'] == 24


def test_family_trend_weekly_and_monthly(conn):
    db.upsert_workout_instance(conn, W1, EXERCISES)
    db.upsert_workout_instance(conn, W2, EXERCISES)
    weekly = q.family_trend(conn, 'm1', 'Push-up')
    assert [(r['period'], r['total_reps']) for r in weekly] == [('2025-01-06', 30), ('2025-01-13', 24)]
    monthly = q.family_trend(conn, 'm1', 'Push-up', 'month_start')
    assert [(r['period'], r['total_reps']) for r in monthly] == [('2025-01-01', 54)]


def test_section_type_comes_from_section_name(conn):
    db.upsert_workout_instance(conn, W1, EXERCISES)
    assert {r['section_type'] for r in q.workout_exercises(conn, 'w1')} == {'main'}


def test_default_db_path():
    assert db.get_db_path() == "/share/FitnessClub/Analytics/workouts.sqlite"


def test_foreign_keys_enforced(conn):
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO fact_exercise_performance (workout_key, member_key, exercise_key, date_key,"
                     " performed_ts, section_seq, exercise_seq) VALUES (999,999,999,20250101,'x',0,0)")
