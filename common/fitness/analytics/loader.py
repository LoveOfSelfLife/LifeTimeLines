from typing import Any
from typing import Optional
import json
import sqlite3


def import_exercise(conn: sqlite3.Connection, exercise: dict) -> None:
    exercise_id = exercise["id"]

    conn.execute("""
        INSERT OR REPLACE INTO exercise (
            id,
            name,
            category,
            equipment,
            equipment_detail,
            force,
            level,
            mechanic,
            set_completion_measure,
            instructions
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        exercise_id,
        exercise.get("name"),
        exercise.get("category"),
        exercise.get("equipment"),
        exercise.get("equipment_detail"),
        exercise.get("force"),
        exercise.get("level"),
        exercise.get("mechanic"),
        exercise.get("setCompletionMeasure"),
        exercise.get("instructions"),
    ))

    conn.execute("""
        INSERT INTO raw_import(source_type, source_id, raw_json)
        VALUES (?, ?, ?)
    """, (
        "exercise",
        exercise_id,
        json.dumps(exercise),
    ))

    # Replace images for this exercise.
    conn.execute("DELETE FROM exercise_image WHERE exercise_id = ?", (exercise_id,))

    for image in exercise.get("images", []):
        conn.execute("""
            INSERT INTO exercise_image (
                exercise_id,
                image_type,
                description,
                url
            )
            VALUES (?, ?, ?, ?)
        """, (
            exercise_id,
            image.get("type"),
            image.get("description"),
            image.get("url"),
        ))

    # Replace muscle links.
    conn.execute("DELETE FROM exercise_muscle WHERE exercise_id = ?", (exercise_id,))

    for muscle_name in exercise.get("primaryMuscles", []):
        muscle_id = get_or_create_muscle(conn, muscle_name)
        conn.execute("""
            INSERT OR REPLACE INTO exercise_muscle (
                exercise_id,
                muscle_id,
                role,
                weight
            )
            VALUES (?, ?, ?, ?)
        """, (
            exercise_id,
            muscle_id,
            "primary",
            1.0,
        ))

    for muscle_name in exercise.get("secondaryMuscles", []):
        muscle_id = get_or_create_muscle(conn, muscle_name)
        conn.execute("""
            INSERT OR REPLACE INTO exercise_muscle (
                exercise_id,
                muscle_id,
                role,
                weight
            )
            VALUES (?, ?, ?, ?)
        """, (
            exercise_id,
            muscle_id,
            "secondary",
            0.5,
        ))

    # Replace fitness component links.
    conn.execute(
        "DELETE FROM exercise_fitness_component WHERE exercise_id = ?",
        (exercise_id,),
    )

    for component_name in exercise.get("physical_fitness_components", []):
        row = conn.execute(
            "SELECT id FROM fitness_component WHERE name = ?",
            (component_name,),
        ).fetchone()

        if row is None:
            conn.execute(
                "INSERT INTO fitness_component(name) VALUES (?)",
                (component_name,),
            )
            row = conn.execute(
                "SELECT id FROM fitness_component WHERE name = ?",
                (component_name,),
            ).fetchone()

        conn.execute("""
            INSERT OR REPLACE INTO exercise_fitness_component (
                exercise_id,
                fitness_component_id,
                weight
            )
            VALUES (?, ?, ?)
        """, (
            exercise_id,
            int(row[0]),
            1.0,
        ))


def import_workout(conn: sqlite3.Connection, workout: dict) -> None:
    workout_id = workout["id"]
    member_id = workout["member_id"]

    conn.execute(
        "INSERT OR IGNORE INTO member(id, display_name) VALUES (?, ?)",
        (member_id, None),
    )

    conn.execute("""
        INSERT OR REPLACE INTO workout_session (
            id,
            member_id,
            source_timestamp,
            started_ts,
            finished_ts,
            member_program_id,
            member_program_name,
            member_workout_def_id,
            scheduled_workout_event_id,
            workout_name,
            raw_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        workout_id,
        member_id,
        workout.get("Timestamp"),
        workout.get("started_ts"),
        workout.get("finished_ts"),
        workout.get("member_program_id"),
        workout.get("member_program_name"),
        workout.get("member_workout_def_id"),
        workout.get("scheduled_workout_event_id"),
        workout.get("name"),
        json.dumps(workout),
    ))

    conn.execute("""
        INSERT INTO raw_import(source_type, source_id, raw_json)
        VALUES (?, ?, ?)
    """, (
        "workout_session",
        workout_id,
        json.dumps(workout),
    ))

    # Rebuild nested workout details for this workout.
    conn.execute(
        "DELETE FROM workout_exercise WHERE workout_session_id = ?",
        (workout_id,),
    )
    conn.execute(
        "DELETE FROM workout_section WHERE workout_session_id = ?",
        (workout_id,),
    )

    for section_index, section in enumerate(workout.get("workout_sections", []), start=1):
        section_name = section.get("name", "")

        cursor = conn.execute("""
            INSERT INTO workout_section (
                workout_session_id,
                section_name,
                section_order
            )
            VALUES (?, ?, ?)
        """, (
            workout_id,
            section_name,
            section_index,
        ))

        workout_section_id = cursor.lastrowid

        for exercise_index, workout_exercise in enumerate(section.get("exercises", []), start=1):
            parameters = workout_exercise.get("parameters", {}) or {}

            conn.execute("""
                INSERT INTO workout_exercise (
                    workout_session_id,
                    workout_section_id,
                    exercise_id,
                    section_name,
                    section_order,
                    exercise_order,

                    sets,
                    reps,
                    time_value,
                    time_unit,
                    force_value,
                    force_unit,
                    pace_value,
                    pace_unit,
                    distance_value,
                    distance_unit,

                    raw_parameters_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                workout_id,
                workout_section_id,
                workout_exercise.get("id"),
                section_name,
                section_index,
                exercise_index,

                to_float(parameters.get("S")),
                to_float(parameters.get("R")),
                to_float(parameters.get("T")),
                parameters.get("Tu"),
                to_float(parameters.get("F")),
                parameters.get("Fu"),
                to_float(parameters.get("P")),
                parameters.get("Pu"),
                to_float(parameters.get("D")),
                parameters.get("Du"),

                json.dumps(parameters),
            ))


def get_or_create_muscle(conn: sqlite3.Connection, name: str) -> int:
    conn.execute("INSERT OR IGNORE INTO muscle(name) VALUES (?)", (name,))
    row = conn.execute(
        "SELECT id FROM muscle WHERE name = ?",
        (name,),
    ).fetchone()
    return int(row[0])


def to_float(value: Any) -> Optional[float]:
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None