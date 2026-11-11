"""Reporting queries over the exercise analytics star schema (see exercise_analytics_db). All return lists of dicts."""


def _rows(conn, sql, params):
    return [dict(r) for r in conn.execute(sql, params).fetchall()]


def exercise_history(conn, member_id, exercise_id):
    """Q1: each time the member performed the exercise, with its parameters, most recent first"""
    return _rows(conn, """
        SELECT f.performed_ts, f.sets, f.reps, f.weight_raw, f.weight_unit, f.weight_kg, f.time_sec, f.tempo,
               f.total_reps, f.total_time_sec, f.volume_kg, f.volume_kind, w.workout_instance_id
        FROM fact_exercise_performance f
        JOIN dim_member m   ON m.member_key = f.member_key
        JOIN dim_exercise e ON e.exercise_key = f.exercise_key
        JOIN dim_workout w  ON w.workout_key = f.workout_key
        WHERE m.member_id = :member_id AND e.exercise_id = :exercise_id
        ORDER BY f.performed_ts DESC, f.section_seq, f.exercise_seq""",
        {'member_id': member_id, 'exercise_id': exercise_id})


def muscle_history(conn, member_id, muscle):
    """Q2: exercises the member performed that impacted the muscle, with parameters"""
    return _rows(conn, """
        SELECT f.performed_ts, e.exercise_id, e.name, f.sets, f.reps, f.weight_kg, f.time_sec, f.volume_kg,
               f.volume_kind
        FROM fact_exercise_performance f
        JOIN dim_member m  ON m.member_key = f.member_key
        JOIN dim_exercise e ON e.exercise_key = f.exercise_key
        JOIN bridge_exercise_muscle b ON b.exercise_key = f.exercise_key
        JOIN dim_muscle mu ON mu.muscle_key = b.muscle_key
        WHERE m.member_id = :member_id AND mu.muscle = :muscle
        ORDER BY f.performed_ts DESC""", {'member_id': member_id, 'muscle': muscle})


def workout_exercises(conn, workout_instance_id):
    """Q3: all exercises performed in the workout instance, in workout order"""
    return _rows(conn, """
        SELECT f.section_seq, f.section_type, f.exercise_seq, e.exercise_id, e.name,
               f.sets, f.reps, f.weight_raw, f.weight_unit, f.weight_kg, f.time_sec, f.tempo, f.volume_kg
        FROM fact_exercise_performance f
        JOIN dim_workout w  ON w.workout_key = f.workout_key
        JOIN dim_exercise e ON e.exercise_key = f.exercise_key
        WHERE w.workout_instance_id = :wid
        ORDER BY f.section_seq, f.exercise_seq""", {'wid': workout_instance_id})


def workout_muscles(conn, workout_instance_id):
    """Q4: muscles impacted by the workout, with several aggregate measures to choose from"""
    return _rows(conn, """
        SELECT mu.muscle,
               COUNT(*)         AS exercise_count,
               SUM(f.sets)      AS total_sets,
               SUM(f.total_reps) AS total_reps,
               SUM(f.volume_kg) AS volume_kg
        FROM fact_exercise_performance f
        JOIN dim_workout w ON w.workout_key = f.workout_key
        JOIN bridge_exercise_muscle b ON b.exercise_key = f.exercise_key
        JOIN dim_muscle mu ON mu.muscle_key = b.muscle_key
        WHERE w.workout_instance_id = :wid
        GROUP BY mu.muscle
        ORDER BY total_sets DESC, mu.muscle""", {'wid': workout_instance_id})


def workout_fitness_components(conn, workout_instance_id):
    """Q5: how the workout's exercises in aggregate impact the physical fitness components.
    allocated_sets splits each exercise's sets across its components, so it adds up to the workout's sets"""
    return _rows(conn, """
        SELECT c.component,
               COUNT(*)                AS exercise_count,
               SUM(f.sets)             AS total_sets,
               SUM(f.sets * b.share)   AS allocated_sets,
               ROUND(100.0 * SUM(f.sets * b.share) / SUM(SUM(f.sets * b.share)) OVER (), 1) AS pct
        FROM fact_exercise_performance f
        JOIN dim_workout w ON w.workout_key = f.workout_key
        JOIN bridge_exercise_fitness_component b ON b.exercise_key = f.exercise_key
        JOIN dim_fitness_component c ON c.fitness_component_key = b.fitness_component_key
        WHERE w.workout_instance_id = :wid
        GROUP BY c.component
        ORDER BY allocated_sets DESC, c.component""", {'wid': workout_instance_id})


def workout_movements(conn, workout_instance_id, rollup=True):
    """Q6: PUSH vs PULL vs SQUAT ... for the workout. rollup=True groups PUSH-HORZ/PUSH-VERT into PUSH"""
    col = 'mc.parent_code' if rollup else 'mc.code'
    return _rows(conn, f"""
        SELECT {col} AS movement,
               COUNT(*)              AS exercise_count,
               SUM(f.sets * b.share) AS allocated_sets,
               ROUND(100.0 * SUM(f.sets * b.share) / SUM(SUM(f.sets * b.share)) OVER (), 1) AS pct
        FROM fact_exercise_performance f
        JOIN dim_workout w ON w.workout_key = f.workout_key
        JOIN bridge_exercise_movement_category b ON b.exercise_key = f.exercise_key
        JOIN dim_movement_category mc ON mc.movement_category_key = b.movement_category_key
        WHERE w.workout_instance_id = :wid
        GROUP BY {col}
        ORDER BY allocated_sets DESC, movement""", {'wid': workout_instance_id})


def family_trend(conn, member_id, family, period='week_start'):
    """volume trend of an exercise family; period is a dim_date column: date, week_start or month_start"""
    if period not in ('date', 'week_start', 'month_start'):
        raise ValueError(period)
    return _rows(conn, f"""
        SELECT d.{period} AS period, SUM(f.volume_kg) AS volume_kg, SUM(f.total_reps) AS total_reps,
               SUM(f.sets) AS total_sets
        FROM fact_exercise_performance f
        JOIN dim_member m   ON m.member_key = f.member_key
        JOIN dim_exercise e ON e.exercise_key = f.exercise_key
        JOIN dim_date d     ON d.date_key = f.date_key
        WHERE m.member_id = :member_id AND COALESCE(e.family, e.name) = :family
        GROUP BY d.{period} ORDER BY d.{period}""", {'member_id': member_id, 'family': family})


# ---------- queries behind the Exercise History page ----------

NO_GROUP = '(none)'

GROUP_BY_OPTIONS = {
    'exercise': 'No grouping (individual exercises)',
    # 'family': 'Exercise family',
    'movement': 'Movement pattern',
    'muscle': 'Primary muscle',
    'equipment': 'Equipment',
}

# group_by -> (extra joins, expression naming the group). Left joins put exercises lacking the
# classification into NO_GROUP; an exercise with several values counts fully in each of its groups.
_GROUPINGS = {
    'family': ("", "COALESCE(e.family, e.name)"),
    'exercise': ("", "e.name"),
    'movement': ("LEFT JOIN bridge_exercise_movement_category gb ON gb.exercise_key = f.exercise_key"
                 " LEFT JOIN dim_movement_category gd ON gd.movement_category_key = gb.movement_category_key",
                 f"COALESCE(gd.code, '{NO_GROUP}')"),
    'muscle': ("LEFT JOIN bridge_exercise_muscle gb ON gb.exercise_key = f.exercise_key"
               " LEFT JOIN dim_muscle gd ON gd.muscle_key = gb.muscle_key",
               f"COALESCE(gd.muscle, '{NO_GROUP}')"),
    'equipment': ("LEFT JOIN bridge_exercise_equipment gb ON gb.exercise_key = f.exercise_key"
                  " LEFT JOIN dim_equipment gd ON gd.equipment_key = gb.equipment_key",
                  f"COALESCE(gd.equipment, '{NO_GROUP}')"),
}

# the natural volume of a fact row depends on what was recorded for it
VOLUME_EXPR = ("CASE f.volume_kind WHEN 'load' THEN f.volume_kg WHEN 'reps' THEN f.total_reps"
               " WHEN 'time' THEN f.total_time_sec END")

_FROM = ("FROM fact_exercise_performance f"
         " JOIN dim_member m ON m.member_key = f.member_key"
         " JOIN dim_exercise e ON e.exercise_key = f.exercise_key"
         " JOIN dim_workout w ON w.workout_key = f.workout_key"
         " JOIN dim_date d ON d.date_key = f.date_key")

PERIOD_EXPR = {'workout': 'w.started_ts', 'week': 'd.week_start', 'month': 'd.month_start'}


def _grouping(group_by):
    if group_by not in _GROUPINGS:
        raise ValueError(f"unknown group_by: {group_by}")
    return _GROUPINGS[group_by]


def _volumes(rows_by_kind):
    return [{'kind': kind, 'value': round(value, 1)} for kind, value in rows_by_kind if kind and value]


def group_summaries(conn, member_id, group_by):
    """one row per group: exercises and workouts it covers, last performed, and total volume per volume kind"""
    joins, expr = _grouping(group_by)
    base = _rows(conn, f"""
        SELECT {expr} AS grp, COUNT(DISTINCT f.exercise_key) AS exercise_count,
               COUNT(DISTINCT f.workout_key) AS workout_count, MAX(w.started_ts) AS last_ts
        {_FROM} {joins} WHERE m.member_id = :member_id GROUP BY grp""", {'member_id': member_id})
    kinds = _rows(conn, f"""
        SELECT {expr} AS grp, f.volume_kind AS kind, SUM({VOLUME_EXPR}) AS value
        {_FROM} {joins} WHERE m.member_id = :member_id GROUP BY grp, f.volume_kind""", {'member_id': member_id})
    by_group = {}
    for k in kinds:
        by_group.setdefault(k['grp'], []).append((k['kind'], k['value']))
    out = [{'group': r['grp'], 'exercise_count': r['exercise_count'], 'workout_count': r['workout_count'],
            'last_date': r['last_ts'][:10], 'volumes': _volumes(by_group.get(r['grp'], []))} for r in base]
    out.sort(key=lambda s: (s['group'] == NO_GROUP, s['group'].lower()))
    return out


def _exercise_summaries(conn, joins, where, params):
    base = _rows(conn, f"""
        SELECT e.exercise_id, e.name AS exercise_name, COUNT(DISTINCT f.workout_key) AS workout_count,
               MAX(w.started_ts) AS last_ts
        {_FROM} {joins} WHERE {where}
        GROUP BY e.exercise_id, e.name""", params)
    kinds = _rows(conn, f"""
        SELECT e.exercise_id, f.volume_kind AS kind, SUM({VOLUME_EXPR}) AS value
        {_FROM} {joins} WHERE {where}
        GROUP BY e.exercise_id, f.volume_kind""", params)
    by_ex = {}
    for k in kinds:
        by_ex.setdefault(k['exercise_id'], []).append((k['kind'], k['value']))
    out = [{'exercise_id': r['exercise_id'], 'exercise_name': r['exercise_name'],
            'workout_count': r['workout_count'], 'last_date': r['last_ts'][:10],
            'volumes': _volumes(by_ex.get(r['exercise_id'], []))} for r in base]
    out.sort(key=lambda r: r['exercise_name'].lower())
    return out


def exercise_summaries(conn, member_id):
    """All individual exercises performed by the member."""
    return _exercise_summaries(conn, "", "m.member_id = :member_id", {'member_id': member_id})


def group_exercises(conn, member_id, group_by, group):
    """The exercises within one group, sorted by name."""
    joins, expr = _grouping(group_by)
    return _exercise_summaries(conn, joins, f"m.member_id = :member_id AND {expr} = :grp",
                               {'member_id': member_id, 'grp': group})


def exercise_name(conn, exercise_id):
    row = conn.execute("SELECT name FROM dim_exercise WHERE exercise_id = ?", (exercise_id,)).fetchone()
    return row[0] if row else exercise_id


def time_series(conn, member_id, metric='volume', resolution='workout', group_by=None, group=None,
                exercise_id=None):
    """
    rows of {period, series, value} for charting, for one group or one exercise.
    volume gets one series per volume kind (kg x reps, reps and seconds can't be added together).
    resolution: workout (one point per workout), week or month.
    """
    if resolution not in PERIOD_EXPR:
        raise ValueError(f"unknown resolution: {resolution}")
    period = PERIOD_EXPR[resolution]
    params = {'member_id': member_id}
    joins, where = "", "m.member_id = :member_id"
    if exercise_id:
        where += " AND e.exercise_id = :exercise_id"
        params['exercise_id'] = exercise_id
    elif group_by:
        joins, expr = _grouping(group_by)
        where += f" AND {expr} = :grp"
        params['grp'] = group

    if metric == 'reps':
        select, extra, series = "SUM(f.total_reps)", "AND f.total_reps IS NOT NULL", "'Total reps'"
    elif metric == 'sets':
        select, extra, series = "SUM(f.sets)", "", "'Total sets'"
    elif metric == 'max_weight':
        select, extra, series = "MAX(f.weight_kg)", "AND f.weight_kg IS NOT NULL", "'Max weight (kg)'"
    else:
        select, extra = f"SUM({VOLUME_EXPR})", "AND f.volume_kind IS NOT NULL"
        series = ("CASE f.volume_kind WHEN 'load' THEN 'Volume (kg x reps)' WHEN 'reps' THEN 'Volume (bodyweight reps)'"
                  " ELSE 'Volume (seconds)' END")
    return _rows(conn, f"""
        SELECT {period} AS period, {series} AS series, {select} AS value
        {_FROM} {joins} WHERE {where} {extra}
        GROUP BY period, series ORDER BY period""", params)


def exercise_workouts(conn, member_id, exercise_id):
    """the individual workout entries of an exercise, most recent first, ready for display"""
    return exercise_history(conn, member_id, exercise_id)
