import sqlite3
from pathlib import Path

ANALYTICS_TABLES_SQL = """
    PRAGMA foreign_keys = ON;

    CREATE TABLE IF NOT EXISTS member (
        id TEXT PRIMARY KEY,
        display_name TEXT
    );

    CREATE TABLE IF NOT EXISTS exercise (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT,
        equipment TEXT,
        equipment_detail TEXT,
        force TEXT,
        level TEXT,
        mechanic TEXT,
        set_completion_measure TEXT,
        instructions TEXT
    );

    CREATE TABLE IF NOT EXISTS exercise_image (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        exercise_id TEXT NOT NULL,
        image_type TEXT,
        description TEXT,
        url TEXT,
        FOREIGN KEY (exercise_id) REFERENCES exercise(id)
    );

    CREATE TABLE IF NOT EXISTS muscle (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    );

    CREATE TABLE IF NOT EXISTS exercise_muscle (
        exercise_id TEXT NOT NULL,
        muscle_id INTEGER NOT NULL,
        role TEXT,
        weight REAL DEFAULT 1.0,
        PRIMARY KEY (exercise_id, muscle_id, role),
        FOREIGN KEY (exercise_id) REFERENCES exercise(id),
        FOREIGN KEY (muscle_id) REFERENCES muscle(id)
    );

    CREATE TABLE IF NOT EXISTS fitness_component (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    );

    CREATE TABLE IF NOT EXISTS exercise_fitness_component (
        exercise_id TEXT NOT NULL,
        fitness_component_id INTEGER NOT NULL,
        weight REAL DEFAULT 1.0,
        PRIMARY KEY (exercise_id, fitness_component_id),
        FOREIGN KEY (exercise_id) REFERENCES exercise(id),
        FOREIGN KEY (fitness_component_id) REFERENCES fitness_component(id)
    );

    CREATE TABLE IF NOT EXISTS workout_session (
        id TEXT PRIMARY KEY,
        member_id TEXT NOT NULL,
        source_timestamp TEXT,
        started_ts TEXT,
        finished_ts TEXT,
        member_program_id TEXT,
        member_program_name TEXT,
        member_workout_def_id TEXT,
        scheduled_workout_event_id TEXT,
        workout_name TEXT,
        raw_json TEXT,
        FOREIGN KEY (member_id) REFERENCES member(id)
    );

    CREATE TABLE IF NOT EXISTS workout_section (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workout_session_id TEXT NOT NULL,
        section_name TEXT NOT NULL,
        section_order INTEGER NOT NULL,
        FOREIGN KEY (workout_session_id) REFERENCES workout_session(id)
    );

    CREATE TABLE IF NOT EXISTS workout_exercise (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workout_session_id TEXT NOT NULL,
        workout_section_id INTEGER NOT NULL,
        exercise_id TEXT NOT NULL,
        section_name TEXT NOT NULL,
        section_order INTEGER NOT NULL,
        exercise_order INTEGER NOT NULL,

        sets REAL,
        reps REAL,
        time_value REAL,
        time_unit TEXT,
        force_value REAL,
        force_unit TEXT,
        pace_value REAL,
        pace_unit TEXT,
        distance_value REAL,
        distance_unit TEXT,

        raw_parameters_json TEXT,

        FOREIGN KEY (workout_session_id) REFERENCES workout_session(id),
        FOREIGN KEY (workout_section_id) REFERENCES workout_section(id),
        FOREIGN KEY (exercise_id) REFERENCES exercise(id)
    );

    CREATE TABLE IF NOT EXISTS raw_import (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_type TEXT,
        source_id TEXT,
        imported_at TEXT DEFAULT CURRENT_TIMESTAMP,
        raw_json TEXT NOT NULL
    );
    """

ANALYTICS_VIEWS_SQL = """
PRAGMA foreign_keys = ON;

DROP VIEW IF EXISTS v_workout_session_summary;
DROP VIEW IF EXISTS v_member_exercise_performance;
DROP VIEW IF EXISTS v_member_fitness_component_activity;
DROP VIEW IF EXISTS v_member_muscle_activity;
DROP VIEW IF EXISTS v_workout_exercise_enriched;

CREATE VIEW v_workout_exercise_enriched AS
SELECT
    ws.id AS workout_session_id,
    ws.member_id,
    date(ws.started_ts) AS workout_date,
    ws.started_ts,
    ws.finished_ts,
    ws.member_program_id,
    ws.member_program_name,
    ws.member_workout_def_id,
    ws.scheduled_workout_event_id,
    ws.workout_name,

    we.id AS workout_exercise_id,
    we.workout_section_id,
    we.exercise_id,
    e.name AS exercise_name,
    e.category AS exercise_category,
    e.equipment,
    e.equipment_detail,
    e.force AS exercise_force_type,
    e.level,
    e.mechanic,
    e.set_completion_measure,

    we.section_name,
    we.section_order,
    we.exercise_order,

    we.sets,
    we.reps,
    we.time_value,
    we.time_unit,
    we.force_value,
    we.force_unit,
    we.pace_value,
    we.pace_unit,
    we.distance_value,
    we.distance_unit,

    CASE
        WHEN we.reps IS NOT NULL
        THEN COALESCE(we.sets, 1) * we.reps
        ELSE NULL
    END AS estimated_total_reps,

    CASE
        WHEN we.time_value IS NOT NULL
        THEN COALESCE(we.sets, 1) * we.time_value
        ELSE NULL
    END AS estimated_total_time,

    CASE
        WHEN we.distance_value IS NOT NULL
        THEN COALESCE(we.sets, 1) * we.distance_value
        ELSE NULL
    END AS estimated_total_distance,

    CASE
        WHEN we.reps IS NOT NULL
         AND we.force_value IS NOT NULL
        THEN COALESCE(we.sets, 1) * we.reps * we.force_value
        ELSE NULL
    END AS estimated_strength_volume,

    CASE
        WHEN we.reps IS NOT NULL
         AND we.force_value IS NOT NULL
        THEN COALESCE(we.sets, 1) * we.reps * we.force_value

        WHEN we.reps IS NOT NULL
        THEN COALESCE(we.sets, 1) * we.reps

        WHEN we.time_value IS NOT NULL
        THEN COALESCE(we.sets, 1) * we.time_value

        WHEN we.distance_value IS NOT NULL
        THEN COALESCE(we.sets, 1) * we.distance_value

        ELSE 0
    END AS estimated_activity_quantity,

    we.raw_parameters_json

FROM workout_exercise we
JOIN workout_session ws
    ON ws.id = we.workout_session_id
LEFT JOIN exercise e
    ON e.id = we.exercise_id;


CREATE VIEW v_workout_session_summary AS
SELECT
    ws.id AS workout_session_id,
    ws.member_id,
    date(ws.started_ts) AS workout_date,
    ws.started_ts,
    ws.finished_ts,
    ws.member_program_id,
    ws.member_program_name,
    ws.member_workout_def_id,
    ws.scheduled_workout_event_id,
    ws.workout_name,

    COUNT(we.id) AS exercise_count,
    COUNT(DISTINCT we.section_name) AS section_count,

    SUM(COALESCE(we.sets, 0)) AS total_sets,

    SUM(
        CASE
            WHEN we.reps IS NOT NULL
            THEN COALESCE(we.sets, 1) * we.reps
            ELSE 0
        END
    ) AS total_reps,

    SUM(
        CASE
            WHEN we.time_value IS NOT NULL
            THEN COALESCE(we.sets, 1) * we.time_value
            ELSE 0
        END
    ) AS total_time_value,

    SUM(
        CASE
            WHEN we.distance_value IS NOT NULL
            THEN COALESCE(we.sets, 1) * we.distance_value
            ELSE 0
        END
    ) AS total_distance_value,

    SUM(
        CASE
            WHEN we.reps IS NOT NULL
             AND we.force_value IS NOT NULL
            THEN COALESCE(we.sets, 1) * we.reps * we.force_value
            ELSE 0
        END
    ) AS estimated_strength_volume,

    SUM(
        CASE
            WHEN we.reps IS NOT NULL
             AND we.force_value IS NOT NULL
            THEN COALESCE(we.sets, 1) * we.reps * we.force_value

            WHEN we.reps IS NOT NULL
            THEN COALESCE(we.sets, 1) * we.reps

            WHEN we.time_value IS NOT NULL
            THEN COALESCE(we.sets, 1) * we.time_value

            WHEN we.distance_value IS NOT NULL
            THEN COALESCE(we.sets, 1) * we.distance_value

            ELSE 0
        END
    ) AS estimated_activity_quantity,

    CASE
        WHEN ws.started_ts IS NOT NULL
         AND ws.finished_ts IS NOT NULL
        THEN
            ROUND(
                (julianday(ws.finished_ts) - julianday(ws.started_ts)) * 24 * 60,
                2
            )
        ELSE NULL
    END AS session_duration_minutes

FROM workout_session ws
LEFT JOIN workout_exercise we
    ON we.workout_session_id = ws.id

GROUP BY
    ws.id,
    ws.member_id,
    date(ws.started_ts),
    ws.started_ts,
    ws.finished_ts,
    ws.member_program_id,
    ws.member_program_name,
    ws.member_workout_def_id,
    ws.scheduled_workout_event_id,
    ws.workout_name;


CREATE VIEW v_member_exercise_performance AS
SELECT
    ws.member_id,
    ws.id AS workout_session_id,
    date(ws.started_ts) AS workout_date,
    ws.started_ts,
    ws.finished_ts,
    ws.member_program_name,
    ws.workout_name,

    we.id AS workout_exercise_id,
    we.exercise_id,
    e.name AS exercise_name,
    e.category AS exercise_category,
    e.equipment,
    e.equipment_detail,
    e.set_completion_measure,

    we.section_name,
    we.section_order,
    we.exercise_order,

    we.sets,
    we.reps,
    we.time_value,
    we.time_unit,
    we.force_value,
    we.force_unit,
    we.pace_value,
    we.pace_unit,
    we.distance_value,
    we.distance_unit,

    CASE
        WHEN we.reps IS NOT NULL
        THEN COALESCE(we.sets, 1) * we.reps
        ELSE NULL
    END AS estimated_total_reps,

    CASE
        WHEN we.time_value IS NOT NULL
        THEN COALESCE(we.sets, 1) * we.time_value
        ELSE NULL
    END AS estimated_time_volume,

    CASE
        WHEN we.distance_value IS NOT NULL
        THEN COALESCE(we.sets, 1) * we.distance_value
        ELSE NULL
    END AS estimated_distance_volume,

    CASE
        WHEN we.reps IS NOT NULL
         AND we.force_value IS NOT NULL
        THEN COALESCE(we.sets, 1) * we.reps * we.force_value
        ELSE NULL
    END AS estimated_strength_volume,

    CASE
        WHEN we.reps IS NOT NULL
         AND we.force_value IS NOT NULL
        THEN COALESCE(we.sets, 1) * we.reps * we.force_value

        WHEN we.reps IS NOT NULL
        THEN COALESCE(we.sets, 1) * we.reps

        WHEN we.time_value IS NOT NULL
        THEN COALESCE(we.sets, 1) * we.time_value

        WHEN we.distance_value IS NOT NULL
        THEN COALESCE(we.sets, 1) * we.distance_value

        ELSE 0
    END AS estimated_activity_quantity,

    we.raw_parameters_json

FROM workout_exercise we
JOIN workout_session ws
    ON ws.id = we.workout_session_id
LEFT JOIN exercise e
    ON e.id = we.exercise_id;


CREATE VIEW v_member_fitness_component_activity AS
SELECT
    ws.member_id,
    date(ws.started_ts) AS workout_date,
    fc.name AS fitness_component,

    COUNT(we.id) AS exercise_occurrences,

    SUM(
        COALESCE(we.sets, 0) * COALESCE(efc.weight, 1.0)
    ) AS total_sets,

    SUM(
        CASE
            WHEN we.reps IS NOT NULL
            THEN COALESCE(we.sets, 1) * we.reps * COALESCE(efc.weight, 1.0)
            ELSE 0
        END
    ) AS weighted_reps,

    SUM(
        CASE
            WHEN we.time_value IS NOT NULL
            THEN COALESCE(we.sets, 1) * we.time_value * COALESCE(efc.weight, 1.0)
            ELSE 0
        END
    ) AS weighted_time,

    SUM(
        CASE
            WHEN we.distance_value IS NOT NULL
            THEN COALESCE(we.sets, 1) * we.distance_value * COALESCE(efc.weight, 1.0)
            ELSE 0
        END
    ) AS weighted_distance,

    SUM(
        CASE
            WHEN we.reps IS NOT NULL
             AND we.force_value IS NOT NULL
            THEN COALESCE(we.sets, 1) * we.reps * we.force_value * COALESCE(efc.weight, 1.0)
            ELSE 0
        END
    ) AS weighted_strength_volume,

    SUM(
        CASE
            WHEN we.reps IS NOT NULL
             AND we.force_value IS NOT NULL
            THEN COALESCE(we.sets, 1) * we.reps * we.force_value * COALESCE(efc.weight, 1.0)

            WHEN we.reps IS NOT NULL
            THEN COALESCE(we.sets, 1) * we.reps * COALESCE(efc.weight, 1.0)

            WHEN we.time_value IS NOT NULL
            THEN COALESCE(we.sets, 1) * we.time_value * COALESCE(efc.weight, 1.0)

            WHEN we.distance_value IS NOT NULL
            THEN COALESCE(we.sets, 1) * we.distance_value * COALESCE(efc.weight, 1.0)

            ELSE 0
        END
    ) AS weighted_activity_quantity

FROM workout_exercise we
JOIN workout_session ws
    ON ws.id = we.workout_session_id
JOIN exercise_fitness_component efc
    ON efc.exercise_id = we.exercise_id
JOIN fitness_component fc
    ON fc.id = efc.fitness_component_id

GROUP BY
    ws.member_id,
    date(ws.started_ts),
    fc.name;


CREATE VIEW v_member_muscle_activity AS
SELECT
    ws.member_id,
    date(ws.started_ts) AS workout_date,
    m.name AS muscle,
    em.role,

    COUNT(we.id) AS exercise_occurrences,

    SUM(
        COALESCE(we.sets, 0) * COALESCE(em.weight, 1.0)
    ) AS weighted_sets,

    SUM(
        CASE
            WHEN we.reps IS NOT NULL
            THEN COALESCE(we.sets, 1) * we.reps * COALESCE(em.weight, 1.0)
            ELSE 0
        END
    ) AS weighted_reps,

    SUM(
        CASE
            WHEN we.time_value IS NOT NULL
            THEN COALESCE(we.sets, 1) * we.time_value * COALESCE(em.weight, 1.0)
            ELSE 0
        END
    ) AS weighted_time,

    SUM(
        CASE
            WHEN we.distance_value IS NOT NULL
            THEN COALESCE(we.sets, 1) * we.distance_value * COALESCE(em.weight, 1.0)
            ELSE 0
        END
    ) AS weighted_distance,

    SUM(
        CASE
            WHEN we.reps IS NOT NULL
             AND we.force_value IS NOT NULL
            THEN COALESCE(we.sets, 1) * we.reps * we.force_value * COALESCE(em.weight, 1.0)
            ELSE 0
        END
    ) AS weighted_strength_volume,

    SUM(
        CASE
            WHEN we.reps IS NOT NULL
             AND we.force_value IS NOT NULL
            THEN COALESCE(we.sets, 1) * we.reps * we.force_value * COALESCE(em.weight, 1.0)

            WHEN we.reps IS NOT NULL
            THEN COALESCE(we.sets, 1) * we.reps * COALESCE(em.weight, 1.0)

            WHEN we.time_value IS NOT NULL
            THEN COALESCE(we.sets, 1) * we.time_value * COALESCE(em.weight, 1.0)

            WHEN we.distance_value IS NOT NULL
            THEN COALESCE(we.sets, 1) * we.distance_value * COALESCE(em.weight, 1.0)

            ELSE 0
        END
    ) AS weighted_activity_quantity

FROM workout_exercise we
JOIN workout_session ws
    ON ws.id = we.workout_session_id
JOIN exercise_muscle em
    ON em.exercise_id = we.exercise_id
JOIN muscle m
    ON m.id = em.muscle_id

GROUP BY
    ws.member_id,
    date(ws.started_ts),
    m.name,
    em.role;
"""
FITNESS_COMPONENTS = [
    "flexibility",
    "mobility",
    "balance",
    "core",
    "power",
    "strength",
    "cardio",
    "endurance",
    "myofascia",
    "warmup",
]
def create_analytics_views(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(ANALYTICS_TABLES_SQL)
    conn.executescript(ANALYTICS_VIEWS_SQL)

    for component in FITNESS_COMPONENTS:
        conn.execute(
            "INSERT OR IGNORE INTO fitness_component(name) VALUES (?)",
            (component,),
        )

    conn.commit()
    