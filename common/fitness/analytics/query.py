import json
import sqlite3
from pathlib import Path
from typing import Any, Optional


class AFCAnalyticsRepository:
    """
    SQLite-backed analytics query layer for Active Friends Club workout reporting.

    Each public method returns a JSON-serializable Python object:
        - list[dict]
        - dict
    """

    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _query_all(
        self,
        sql: str,
        params: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(sql, params or {}).fetchall()
            return [dict(row) for row in rows]

    def _query_one(
        self,
        sql: str,
        params: Optional[dict[str, Any]] = None,
    ) -> Optional[dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(sql, params or {}).fetchone()
            return dict(row) if row else None

    def to_json(self, data: Any, indent: int = 2) -> str:
        return json.dumps(data, indent=indent, default=str)

    # ---------------------------------------------------------------------
    # A. Workouts per week
    # ---------------------------------------------------------------------

    def workouts_per_week(self, member_id: str) -> list[dict[str, Any]]:
        sql = """
            SELECT
                member_id,
                strftime('%Y-%W', workout_date) AS year_week,
                COUNT(*) AS workout_count,
                SUM(exercise_count) AS total_exercises,
                SUM(total_sets) AS total_sets,
                SUM(total_reps) AS total_reps,
                SUM(estimated_strength_volume) AS total_strength_volume
            FROM v_workout_session_summary
            WHERE member_id = :member_id
            GROUP BY member_id, strftime('%Y-%W', workout_date)
            ORDER BY year_week;
        """
        return self._query_all(sql, {"member_id": member_id})

    # ---------------------------------------------------------------------
    # B. Workouts per month
    # ---------------------------------------------------------------------

    def workouts_per_month(self, member_id: str) -> list[dict[str, Any]]:
        sql = """
            SELECT
                member_id,
                strftime('%Y-%m', workout_date) AS year_month,
                COUNT(*) AS workout_count,
                SUM(exercise_count) AS total_exercises,
                SUM(total_sets) AS total_sets,
                SUM(total_reps) AS total_reps,
                SUM(estimated_strength_volume) AS total_strength_volume
            FROM v_workout_session_summary
            WHERE member_id = :member_id
            GROUP BY member_id, strftime('%Y-%m', workout_date)
            ORDER BY year_month;
        """
        return self._query_all(sql, {"member_id": member_id})

    # ---------------------------------------------------------------------
    # C. Recent workout history
    # ---------------------------------------------------------------------

    def recent_workout_history(
        self,
        member_id: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        sql = """
            SELECT
                workout_date,
                workout_name,
                member_program_name,
                exercise_count,
                total_sets,
                total_reps,
                estimated_strength_volume
            FROM v_workout_session_summary
            WHERE member_id = :member_id
            ORDER BY started_ts DESC
            LIMIT :limit;
        """
        return self._query_all(sql, {"member_id": member_id, "limit": limit})

    # ---------------------------------------------------------------------
    # D. Most frequently performed exercises
    # ---------------------------------------------------------------------

    def most_frequent_exercises(
        self,
        member_id: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        sql = """
            SELECT
                e.name AS exercise_name,
                we.exercise_id,
                COUNT(*) AS times_performed,
                MAX(date(ws.started_ts)) AS last_performed
            FROM workout_exercise we
            JOIN workout_session ws
                ON ws.id = we.workout_session_id
            LEFT JOIN exercise e
                ON e.id = we.exercise_id
            WHERE ws.member_id = :member_id
            GROUP BY e.name, we.exercise_id
            ORDER BY times_performed DESC, last_performed DESC
            LIMIT :limit;
        """
        return self._query_all(sql, {"member_id": member_id, "limit": limit})

    # ---------------------------------------------------------------------
    # E. Exercise progress over time
    # ---------------------------------------------------------------------

    def exercise_progress(
        self,
        member_id: str,
        exercise_id: str,
    ) -> list[dict[str, Any]]:
        sql = """
            SELECT
                workout_date,
                exercise_name,
                sets,
                reps,
                force_value,
                force_unit,
                time_value,
                time_unit,
                estimated_strength_volume,
                estimated_time_volume
            FROM v_member_exercise_performance
            WHERE member_id = :member_id
              AND exercise_id = :exercise_id
            ORDER BY started_ts;
        """
        return self._query_all(
            sql,
            {
                "member_id": member_id,
                "exercise_id": exercise_id,
            },
        )

    # ---------------------------------------------------------------------
    # F. Best performance for a strength exercise
    # ---------------------------------------------------------------------

    def best_strength_performance(
        self,
        member_id: str,
        exercise_id: str,
    ) -> Optional[dict[str, Any]]:
        sql = """
            SELECT
                workout_date,
                exercise_name,
                sets,
                reps,
                force_value,
                force_unit,
                estimated_strength_volume
            FROM v_member_exercise_performance
            WHERE member_id = :member_id
              AND exercise_id = :exercise_id
              AND estimated_strength_volume IS NOT NULL
            ORDER BY estimated_strength_volume DESC
            LIMIT 1;
        """
        return self._query_one(
            sql,
            {
                "member_id": member_id,
                "exercise_id": exercise_id,
            },
        )

    # ---------------------------------------------------------------------
    # G. Fitness component distribution over last N days
    # ---------------------------------------------------------------------

    def fitness_component_distribution(
        self,
        member_id: str,
        days: int = 30,
    ) -> list[dict[str, Any]]:
        sql = """
            SELECT
                fitness_component,
                SUM(exercise_occurrences) AS exercise_occurrences,
                SUM(total_sets) AS total_sets,
                SUM(weighted_reps) AS total_reps,
                SUM(weighted_time) AS total_time,
                SUM(weighted_strength_volume) AS strength_volume
            FROM v_member_fitness_component_activity
            WHERE member_id = :member_id
              AND workout_date >= date('now', :days_modifier)
            GROUP BY fitness_component
            ORDER BY exercise_occurrences DESC;
        """
        return self._query_all(
            sql,
            {
                "member_id": member_id,
                "days_modifier": f"-{days} days",
            },
        )

    # ---------------------------------------------------------------------
    # H. Fitness component trend by week
    # ---------------------------------------------------------------------

    def fitness_component_trend_by_week(
        self,
        member_id: str,
    ) -> list[dict[str, Any]]:
        sql = """
            SELECT
                strftime('%Y-%W', workout_date) AS year_week,
                fitness_component,
                SUM(exercise_occurrences) AS exercise_occurrences,
                SUM(total_sets) AS total_sets,
                SUM(weighted_reps) AS total_reps,
                SUM(weighted_time) AS total_time,
                SUM(weighted_strength_volume) AS strength_volume
            FROM v_member_fitness_component_activity
            WHERE member_id = :member_id
            GROUP BY year_week, fitness_component
            ORDER BY year_week, fitness_component;
        """
        return self._query_all(sql, {"member_id": member_id})

    # ---------------------------------------------------------------------
    # I. Muscle/body-area distribution over last N days
    # ---------------------------------------------------------------------

    def muscle_distribution(
        self,
        member_id: str,
        days: int = 30,
    ) -> list[dict[str, Any]]:
        sql = """
            SELECT
                muscle,
                SUM(exercise_occurrences) AS exercise_occurrences,
                SUM(weighted_sets) AS total_sets,
                SUM(weighted_reps) AS total_reps,
                SUM(weighted_time) AS total_time,
                SUM(weighted_strength_volume) AS strength_volume
            FROM v_member_muscle_activity
            WHERE member_id = :member_id
              AND workout_date >= date('now', :days_modifier)
            GROUP BY muscle
            ORDER BY exercise_occurrences DESC;
        """
        return self._query_all(
            sql,
            {
                "member_id": member_id,
                "days_modifier": f"-{days} days",
            },
        )

    # ---------------------------------------------------------------------
    # J. Muscle/body-area trend by week
    # ---------------------------------------------------------------------

    def muscle_trend_by_week(
        self,
        member_id: str,
    ) -> list[dict[str, Any]]:
        sql = """
            SELECT
                strftime('%Y-%W', workout_date) AS year_week,
                muscle,
                SUM(exercise_occurrences) AS exercise_occurrences,
                SUM(weighted_sets) AS total_sets,
                SUM(weighted_reps) AS total_reps,
                SUM(weighted_time) AS total_time,
                SUM(weighted_strength_volume) AS strength_volume
            FROM v_member_muscle_activity
            WHERE member_id = :member_id
            GROUP BY year_week, muscle
            ORDER BY year_week, muscle;
        """
        return self._query_all(sql, {"member_id": member_id})

    # ---------------------------------------------------------------------
    # K. Average session size over last N days
    # ---------------------------------------------------------------------

    def average_session_size(
        self,
        member_id: str,
        days: int = 90,
    ) -> Optional[dict[str, Any]]:
        sql = """
            SELECT
                member_id,
                COUNT(*) AS workout_count,
                AVG(exercise_count) AS avg_exercises_per_workout,
                AVG(total_sets) AS avg_sets_per_workout,
                AVG(total_reps) AS avg_reps_per_workout,
                AVG(estimated_strength_volume) AS avg_strength_volume
            FROM v_workout_session_summary
            WHERE member_id = :member_id
              AND workout_date >= date('now', :days_modifier)
            GROUP BY member_id;
        """
        return self._query_one(
            sql,
            {
                "member_id": member_id,
                "days_modifier": f"-{days} days",
            },
        )

    # ---------------------------------------------------------------------
    # L. Workout calendar heatmap
    # ---------------------------------------------------------------------

    def workout_calendar_heatmap(
        self,
        member_id: str,
    ) -> list[dict[str, Any]]:
        sql = """
            SELECT
                workout_date,
                COUNT(*) AS workout_count,
                SUM(total_sets) AS total_sets,
                SUM(total_reps) AS total_reps,
                SUM(estimated_strength_volume) AS total_strength_volume
            FROM v_workout_session_summary
            WHERE member_id = :member_id
            GROUP BY workout_date
            ORDER BY workout_date;
        """
        return self._query_all(sql, {"member_id": member_id})

    # ---------------------------------------------------------------------
    # M. Day-of-week workout pattern
    # ---------------------------------------------------------------------

    def day_of_week_pattern(
        self,
        member_id: str,
    ) -> list[dict[str, Any]]:
        sql = """
            SELECT
                CASE strftime('%w', workout_date)
                    WHEN '0' THEN 'Sunday'
                    WHEN '1' THEN 'Monday'
                    WHEN '2' THEN 'Tuesday'
                    WHEN '3' THEN 'Wednesday'
                    WHEN '4' THEN 'Thursday'
                    WHEN '5' THEN 'Friday'
                    WHEN '6' THEN 'Saturday'
                END AS day_of_week,
                COUNT(*) AS workout_count
            FROM v_workout_session_summary
            WHERE member_id = :member_id
            GROUP BY strftime('%w', workout_date)
            ORDER BY strftime('%w', workout_date);
        """
        return self._query_all(sql, {"member_id": member_id})

    # ---------------------------------------------------------------------
    # N. Workout dates, useful for streak calculation
    # ---------------------------------------------------------------------

    def workout_dates_desc(
        self,
        member_id: str,
    ) -> list[str]:
        sql = """
            SELECT DISTINCT workout_date
            FROM v_workout_session_summary
            WHERE member_id = :member_id
            ORDER BY workout_date DESC;
        """
        rows = self._query_all(sql, {"member_id": member_id})
        return [row["workout_date"] for row in rows]

    # ---------------------------------------------------------------------
    # O. Exercises not performed recently
    # ---------------------------------------------------------------------

    def exercises_not_performed_recently(
        self,
        member_id: str,
        days: int = 30,
    ) -> list[dict[str, Any]]:
        sql = """
            SELECT
                e.id AS exercise_id,
                e.name AS exercise_name,
                MAX(date(ws.started_ts)) AS last_performed
            FROM exercise e
            LEFT JOIN workout_exercise we
                ON we.exercise_id = e.id
            LEFT JOIN workout_session ws
                ON ws.id = we.workout_session_id
               AND ws.member_id = :member_id
            GROUP BY e.id, e.name
            HAVING last_performed IS NULL
                OR last_performed < date('now', :days_modifier)
            ORDER BY last_performed;
        """
        return self._query_all(
            sql,
            {
                "member_id": member_id,
                "days_modifier": f"-{days} days",
            },
        )

    # ---------------------------------------------------------------------
    # P. New exercises added in the last N days
    # ---------------------------------------------------------------------

    def new_exercises_recently(
        self,
        member_id: str,
        days: int = 30,
    ) -> list[dict[str, Any]]:
        sql = """
            WITH first_performed AS (
                SELECT
                    we.exercise_id,
                    e.name AS exercise_name,
                    MIN(date(ws.started_ts)) AS first_date
                FROM workout_exercise we
                JOIN workout_session ws
                    ON ws.id = we.workout_session_id
                LEFT JOIN exercise e
                    ON e.id = we.exercise_id
                WHERE ws.member_id = :member_id
                GROUP BY we.exercise_id, e.name
            )
            SELECT
                exercise_id,
                exercise_name,
                first_date
            FROM first_performed
            WHERE first_date >= date('now', :days_modifier)
            ORDER BY first_date DESC;
        """
        return self._query_all(
            sql,
            {
                "member_id": member_id,
                "days_modifier": f"-{days} days",
            },
        )

    # ---------------------------------------------------------------------
    # Dashboard summary combining several queries
    # ---------------------------------------------------------------------

    def member_dashboard_summary(
        self,
        member_id: str,
    ) -> dict[str, Any]:
        return {
            "member_id": member_id,
            "recent_workouts": self.recent_workout_history(member_id, limit=10),
            "workouts_per_week": self.workouts_per_week(member_id),
            "workouts_per_month": self.workouts_per_month(member_id),
            "most_frequent_exercises": self.most_frequent_exercises(member_id, limit=10),
            "fitness_component_distribution_30_days": self.fitness_component_distribution(member_id, days=30),
            "muscle_distribution_30_days": self.muscle_distribution(member_id, days=30),
            "average_session_size_90_days": self.average_session_size(member_id, days=90),
            "day_of_week_pattern": self.day_of_week_pattern(member_id),
            "calendar_heatmap": self.workout_calendar_heatmap(member_id),
            "new_exercises_30_days": self.new_exercises_recently(member_id, days=30),
        }
    