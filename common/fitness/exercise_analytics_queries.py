"""Reporting queries over the exercise analytics star schema (see exercise_analytics_db). All return lists of dicts."""


def _rows(conn, sql, params):
    return [dict(r) for r in conn.execute(sql, params).fetchall()]


def exercise_history(conn, member_id, exercise_id):
    """Q1: each time the member performed the exercise, with its parameters, most recent first"""
    return _rows(conn, """
        SELECT f.performed_ts, f.sets, f.reps, f.weight_raw, f.weight_unit, f.weight_kg, f.time_sec, f.tempo,
               f.total_reps, f.volume_kg, f.volume_kind, w.workout_instance_id
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
