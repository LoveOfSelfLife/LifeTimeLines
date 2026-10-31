"""
SQLite star schema for reporting on exercises performed by members in workout instances.

The entity store remains the source of truth; these tables are derived and reporting-only.
Everything here can be rebuilt from workout instances (see rebuild_member).
"""
import logging
import sqlite3
from datetime import datetime, timezone

from common.env_context import Env
from common.fitness.exercise_entity import MOVEMENT_CATEGORIES, MUSCLES, PHYSICAL_FITNESS_COMPONENTS

logger = logging.getLogger(__name__)

LBS_TO_KG = 0.45359237

SCHEMA = """
CREATE TABLE IF NOT EXISTS dim_member (
    member_key   INTEGER PRIMARY KEY,
    member_id    TEXT NOT NULL UNIQUE,
    member_name  TEXT
);

CREATE TABLE IF NOT EXISTS dim_date (
    date_key     INTEGER PRIMARY KEY,           -- YYYYMMDD
    date         TEXT NOT NULL,
    year         INTEGER NOT NULL,
    quarter      INTEGER NOT NULL,
    month        INTEGER NOT NULL,
    iso_year     INTEGER NOT NULL,
    iso_week     INTEGER NOT NULL,
    day_of_week  INTEGER NOT NULL,              -- 1=Mon..7=Sun
    week_start   TEXT NOT NULL,                 -- ISO date of the Monday
    month_start  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_workout (
    workout_key           INTEGER PRIMARY KEY,
    workout_instance_id   TEXT NOT NULL UNIQUE,
    member_key            INTEGER NOT NULL REFERENCES dim_member(member_key),
    workout_name          TEXT,
    member_workout_def_id TEXT,
    member_program_id     TEXT,
    member_program_name   TEXT,
    started_ts            TEXT NOT NULL,
    finished_ts           TEXT,
    duration_sec          INTEGER,
    source_updated_ts     TEXT,
    loaded_at             TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_exercise (
    exercise_key   INTEGER PRIMARY KEY,
    exercise_id    TEXT NOT NULL UNIQUE,
    name           TEXT NOT NULL,
    family         TEXT,
    exercise_type  TEXT,
    category       TEXT,
    mechanic       TEXT,
    force          TEXT,
    level          TEXT,
    equipment      TEXT,
    refreshed_at   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_muscle (
    muscle_key  INTEGER PRIMARY KEY,
    muscle      TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS dim_fitness_component (
    fitness_component_key INTEGER PRIMARY KEY,
    component             TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS dim_movement_category (
    movement_category_key INTEGER PRIMARY KEY,
    code         TEXT NOT NULL UNIQUE,
    parent_code  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS bridge_exercise_muscle (
    exercise_key INTEGER NOT NULL REFERENCES dim_exercise(exercise_key) ON DELETE CASCADE,
    muscle_key   INTEGER NOT NULL REFERENCES dim_muscle(muscle_key),
    role         TEXT NOT NULL DEFAULT 'primary' CHECK (role IN ('primary','secondary')),
    PRIMARY KEY (exercise_key, muscle_key, role)
);

CREATE TABLE IF NOT EXISTS bridge_exercise_fitness_component (
    exercise_key          INTEGER NOT NULL REFERENCES dim_exercise(exercise_key) ON DELETE CASCADE,
    fitness_component_key INTEGER NOT NULL REFERENCES dim_fitness_component(fitness_component_key),
    share                 REAL NOT NULL,        -- 1 / number of components of the exercise
    PRIMARY KEY (exercise_key, fitness_component_key)
);

CREATE TABLE IF NOT EXISTS bridge_exercise_movement_category (
    exercise_key          INTEGER NOT NULL REFERENCES dim_exercise(exercise_key) ON DELETE CASCADE,
    movement_category_key INTEGER NOT NULL REFERENCES dim_movement_category(movement_category_key),
    share                 REAL NOT NULL,        -- 1 / number of categories of the exercise
    PRIMARY KEY (exercise_key, movement_category_key)
);

CREATE TABLE IF NOT EXISTS dim_equipment (
    equipment_key INTEGER PRIMARY KEY,
    equipment     TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS bridge_exercise_equipment (
    exercise_key  INTEGER NOT NULL REFERENCES dim_exercise(exercise_key) ON DELETE CASCADE,
    equipment_key INTEGER NOT NULL REFERENCES dim_equipment(equipment_key),
    PRIMARY KEY (exercise_key, equipment_key)
);

-- operational, not part of the star: records that a member's history has been loaded from the entity store
CREATE TABLE IF NOT EXISTS member_build_state (
    member_id  TEXT PRIMARY KEY,
    rebuilt_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_exercise_performance (
    fact_id        INTEGER PRIMARY KEY,
    workout_key    INTEGER NOT NULL REFERENCES dim_workout(workout_key) ON DELETE CASCADE,
    member_key     INTEGER NOT NULL REFERENCES dim_member(member_key),
    exercise_key   INTEGER NOT NULL REFERENCES dim_exercise(exercise_key),
    date_key       INTEGER NOT NULL REFERENCES dim_date(date_key),
    performed_ts   TEXT NOT NULL,
    section_type   TEXT,
    section_seq    INTEGER NOT NULL,
    exercise_seq   INTEGER NOT NULL,
    sets           REAL,
    reps           REAL,
    weight_raw     TEXT,
    weight_unit    TEXT,
    time_sec       REAL,
    tempo          TEXT,
    weight_kg      REAL,
    total_reps     REAL,
    total_time_sec REAL,
    volume_kg      REAL,
    volume_kind    TEXT CHECK (volume_kind IN ('load','reps','time')),
    UNIQUE (workout_key, section_seq, exercise_seq)
);

CREATE INDEX IF NOT EXISTS ix_fact_member_exercise ON fact_exercise_performance (member_key, exercise_key, performed_ts);
CREATE INDEX IF NOT EXISTS ix_fact_member_date     ON fact_exercise_performance (member_key, date_key);
CREATE INDEX IF NOT EXISTS ix_fact_workout         ON fact_exercise_performance (workout_key);
CREATE INDEX IF NOT EXISTS ix_bem_muscle           ON bridge_exercise_muscle (muscle_key, exercise_key);
"""


DEFAULT_DB_PATH = "/share/FitnessClub/Analytics/workouts.sqlite"


def get_db_path():
    return getattr(Env, 'ANALYTICS_DB_PATH', None) or DEFAULT_DB_PATH


def connect(db_path=None):
    """opens the analytics db (default: the file on the share), creating the schema and static dimensions if needed"""
    conn = sqlite3.connect(db_path or get_db_path(), timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    _seed_static_dimensions(conn)
    return conn


def _seed_static_dimensions(conn):
    conn.executemany("INSERT OR IGNORE INTO dim_muscle (muscle) VALUES (?)", [(m,) for m in MUSCLES])
    conn.executemany("INSERT OR IGNORE INTO dim_fitness_component (component) VALUES (?)",
                     [(c,) for c in PHYSICAL_FITNESS_COMPONENTS])
    conn.executemany("INSERT OR IGNORE INTO dim_movement_category (code, parent_code) VALUES (?, ?)",
                     [(c, c.split('-')[0]) for c in MOVEMENT_CATEGORIES])
    conn.commit()


# ---------- value helpers ----------

def _num(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _weight_kg(weight, unit):
    w = _num(weight)
    if w is None:
        return None
    unit = (unit or 'kg').strip().lower()
    if unit in ('kg', 'kgs', 'kilograms'):
        return w
    if unit in ('lb', 'lbs', 'pounds'):
        return w * LBS_TO_KG
    return None


def _as_list(value):
    if not value:
        return []
    if isinstance(value, (list, tuple)):
        return [str(v) for v in value if v]
    return [str(value)]


TIME_UNIT_SECONDS = {'s': 1, 'sec': 1, 'secs': 1, 'second': 1, 'seconds': 1,
                     'm': 60, 'min': 60, 'mins': 60, 'minute': 60, 'minutes': 60,
                     'h': 3600, 'hr': 3600, 'hour': 3600, 'hours': 3600}


def normalize_parameters(parameters):
    """
    The app stores exercise parameters as S, R, F/Fu (force, unit), T/Tu (time, unit), P/Pu (pace);
    older and sample data use sets, reps, weight/weight_unit, time, tempo. Returns the long-name form,
    with time converted to seconds.
    """
    p = parameters or {}

    def pick(*names):
        for n in names:
            if p.get(n) not in (None, ''):
                return p.get(n)
        return None

    time_value = _num(pick('T', 'time'))
    if time_value is not None:
        time_unit = str(pick('Tu', 'time_unit') or 'sec').strip().lower()
        time_value *= TIME_UNIT_SECONDS.get(time_unit, 1)
    pace_unit = str(pick('Pu') or '').strip().lower()
    return {'sets': pick('S', 'sets'), 'reps': pick('R', 'reps'), 'weight': pick('F', 'weight'),
            'weight_unit': pick('Fu', 'weight_unit'), 'time': time_value,
            'tempo': pick('tempo') or (pick('P') if pace_unit == 'tempo' else None)}


def compute_measures(parameters):
    """raw exercise parameters -> the stored measures, including the derived ones"""
    p = normalize_parameters(parameters)
    sets = _num(p.get('sets'))
    reps = _num(p.get('reps'))
    time_sec = _num(p.get('time'))
    weight_kg = _weight_kg(p.get('weight'), p.get('weight_unit'))
    if sets is None:
        sets = 1.0
    total_reps = sets * reps if reps else None
    total_time = sets * time_sec if time_sec else None
    volume_kg = total_reps * weight_kg if (total_reps and weight_kg) else None
    if volume_kg is not None:
        kind = 'load'
    elif total_reps:
        kind = 'reps'
    elif total_time:
        kind = 'time'
    else:
        kind = None
    return {'sets': sets, 'reps': reps, 'time_sec': time_sec, 'weight_kg': weight_kg, 'total_reps': total_reps,
            'total_time_sec': total_time, 'volume_kg': volume_kg, 'volume_kind': kind}


def _parse_ts(ts):
    dt = datetime.fromisoformat(str(ts).replace('Z', '+00:00'))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _now():
    return datetime.now(timezone.utc).isoformat()


# ---------- dimension upserts ----------

def _upsert_member(conn, member_id):
    conn.execute("INSERT OR IGNORE INTO dim_member (member_id) VALUES (?)", (member_id,))
    return conn.execute("SELECT member_key FROM dim_member WHERE member_id = ?", (member_id,)).fetchone()[0]


def _upsert_date(conn, dt):
    iso = dt.isocalendar()
    d = dt.date()
    date_key = d.year * 10000 + d.month * 100 + d.day
    week_start = d.fromordinal(d.toordinal() - (iso[2] - 1))
    conn.execute(
        "INSERT OR IGNORE INTO dim_date (date_key, date, year, quarter, month, iso_year, iso_week, day_of_week,"
        " week_start, month_start) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (date_key, d.isoformat(), d.year, (d.month - 1) // 3 + 1, d.month, iso[0], iso[1], iso[2],
         week_start.isoformat(), d.replace(day=1).isoformat()))
    return date_key


def upsert_exercise(conn, exercise_id, exercise):
    """
    upserts the exercise dimension row and replaces its classification bridges.
    exercise is an ExerciseEntity-like dict, or None if the exercise no longer exists.
    """
    ex = exercise or {}
    name = ex.get('name') or exercise_id
    equipment = ", ".join(_as_list(ex.get('equipment_list'))) or ex.get('equipment')
    conn.execute(
        "INSERT INTO dim_exercise (exercise_id, name, family, exercise_type, category, mechanic, force, level,"
        " equipment, refreshed_at) VALUES (?,?,?,?,?,?,?,?,?,?)"
        " ON CONFLICT(exercise_id) DO UPDATE SET name=excluded.name, family=excluded.family,"
        " exercise_type=excluded.exercise_type, category=excluded.category, mechanic=excluded.mechanic,"
        " force=excluded.force, level=excluded.level, equipment=excluded.equipment,"
        " refreshed_at=excluded.refreshed_at",
        (exercise_id, name, (ex.get('family') or '').strip() or None, ex.get('type'), ex.get('category'),
         ex.get('mechanic'), ex.get('force'), ex.get('level'), equipment, _now()))
    key = conn.execute("SELECT exercise_key FROM dim_exercise WHERE exercise_id = ?", (exercise_id,)).fetchone()[0]

    for table in ('bridge_exercise_muscle', 'bridge_exercise_fitness_component',
                  'bridge_exercise_movement_category', 'bridge_exercise_equipment'):
        conn.execute(f"DELETE FROM {table} WHERE exercise_key = ?", (key,))

    for item in set(_as_list(ex.get('equipment_list'))):
        conn.execute("INSERT OR IGNORE INTO dim_equipment (equipment) VALUES (?)", (item,))
        conn.execute("INSERT INTO bridge_exercise_equipment (exercise_key, equipment_key)"
                     " SELECT ?, equipment_key FROM dim_equipment WHERE equipment = ?", (key, item))

    for muscle in set(_as_list(ex.get('primaryMuscles'))):
        conn.execute("INSERT INTO bridge_exercise_muscle (exercise_key, muscle_key, role)"
                     " SELECT ?, muscle_key, 'primary' FROM dim_muscle WHERE muscle = ?", (key, muscle))

    components = sorted(set(_as_list(ex.get('physical_fitness_components'))))
    for c in components:
        conn.execute("INSERT INTO bridge_exercise_fitness_component (exercise_key, fitness_component_key, share)"
                     " SELECT ?, fitness_component_key, ? FROM dim_fitness_component WHERE component = ?",
                     (key, 1.0 / len(components), c))

    categories = sorted(set(_as_list(ex.get('movement_categories'))))
    for c in categories:
        conn.execute("INSERT INTO bridge_exercise_movement_category (exercise_key, movement_category_key, share)"
                     " SELECT ?, movement_category_key, ? FROM dim_movement_category WHERE code = ?",
                     (key, 1.0 / len(categories), c))
    return key


# ---------- maintenance operations ----------

def upsert_workout_instance(conn, workout_instance, exercises_by_id):
    """
    Idempotent: replaces everything stored for the workout instance with the facts computed from it.
    Unfinished instances (no started_ts or finished_ts) are removed from the db rather than loaded.
    Returns the number of fact rows written.
    exercises_by_id maps exercise id -> ExerciseEntity-like dict (or None).
    """
    wid = workout_instance.get('id')
    member_id = workout_instance.get('member_id')
    if not wid or not member_id:
        raise ValueError("workout instance needs an id and a member_id")
    if not workout_instance.get('started_ts') or not workout_instance.get('finished_ts'):
        delete_workout_instance(conn, wid)
        return 0

    started = _parse_ts(workout_instance['started_ts'])
    finished = _parse_ts(workout_instance['finished_ts'])
    with conn:
        member_key = _upsert_member(conn, member_id)
        date_key = _upsert_date(conn, started)
        conn.execute(
            "INSERT INTO dim_workout (workout_instance_id, member_key, workout_name, member_workout_def_id,"
            " member_program_id, member_program_name, started_ts, finished_ts, duration_sec, source_updated_ts,"
            " loaded_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)"
            " ON CONFLICT(workout_instance_id) DO UPDATE SET member_key=excluded.member_key,"
            " workout_name=excluded.workout_name, member_workout_def_id=excluded.member_workout_def_id,"
            " member_program_id=excluded.member_program_id, member_program_name=excluded.member_program_name,"
            " started_ts=excluded.started_ts, finished_ts=excluded.finished_ts,"
            " duration_sec=excluded.duration_sec, source_updated_ts=excluded.source_updated_ts,"
            " loaded_at=excluded.loaded_at",
            (wid, member_key, workout_instance.get('name'), workout_instance.get('member_workout_def_id'),
             workout_instance.get('member_program_id'), workout_instance.get('member_program_name'),
             started.isoformat(), finished.isoformat(), int((finished - started).total_seconds()),
             workout_instance.get('updated_ts'), _now()))
        workout_key = conn.execute("SELECT workout_key FROM dim_workout WHERE workout_instance_id = ?",
                                   (wid,)).fetchone()[0]
        conn.execute("DELETE FROM fact_exercise_performance WHERE workout_key = ?", (workout_key,))

        exercise_keys = {}
        count = 0
        for section_seq, section in enumerate(workout_instance.get('workout_sections') or []):
            section_type = section.get('name')
            for exercise_seq, item in enumerate(section.get('exercises') or []):
                exercise_id = item.get('id')
                if not exercise_id:
                    continue
                if exercise_id not in exercise_keys:
                    exercise_keys[exercise_id] = upsert_exercise(conn, exercise_id, exercises_by_id.get(exercise_id))
                params = normalize_parameters(item.get('parameters'))
                m = compute_measures(item.get('parameters'))
                conn.execute(
                    "INSERT INTO fact_exercise_performance (workout_key, member_key, exercise_key, date_key,"
                    " performed_ts, section_type, section_seq, exercise_seq, sets, reps, weight_raw, weight_unit,"
                    " time_sec, tempo, weight_kg, total_reps, total_time_sec, volume_kg, volume_kind)"
                    " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (workout_key, member_key, exercise_keys[exercise_id], date_key, started.isoformat(),
                     section_type, section_seq, exercise_seq, m['sets'], m['reps'],
                     None if params.get('weight') is None else str(params.get('weight')),
                     params.get('weight_unit'), m['time_sec'], params.get('tempo'), m['weight_kg'],
                     m['total_reps'], m['total_time_sec'], m['volume_kg'], m['volume_kind']))
                count += 1
    return count


def delete_workout_instance(conn, workout_instance_id):
    """removes the workout and (by cascade) all of its facts. Safe to call for an unknown id."""
    with conn:
        cur = conn.execute("DELETE FROM dim_workout WHERE workout_instance_id = ?", (workout_instance_id,))
    return cur.rowcount


def rebuild_member(conn, member_id, workout_instances, exercises_by_id):
    """
    Makes the db match the given workout instances for the member: loads each finished instance and removes
    any workout the member has in the db that is not among them (e.g. deleted since).
    Returns (workouts_loaded, facts_loaded).
    """
    loaded_ids, facts = set(), 0
    for wi in workout_instances:
        n = upsert_workout_instance(conn, wi, exercises_by_id)
        if wi.get('started_ts') and wi.get('finished_ts'):
            loaded_ids.add(wi['id'])
            facts += n
    existing = conn.execute("SELECT w.workout_instance_id FROM dim_workout w JOIN dim_member m"
                            " ON m.member_key = w.member_key WHERE m.member_id = ?", (member_id,)).fetchall()
    for row in existing:
        if row[0] not in loaded_ids:
            delete_workout_instance(conn, row[0])
    return len(loaded_ids), facts


# ---------- entity-store adapters ----------

def _load_exercises(workout_instances):
    from common.entity_store import EntityStore
    from common.fitness.exercise_entity import ExerciseEntity
    es = EntityStore()
    ids = {i.get('id') for wi in workout_instances for s in (wi.get('workout_sections') or [])
           for i in (s.get('exercises') or []) if i.get('id')}
    return {eid: es.get_item(ExerciseEntity({'id': eid})) for eid in ids}


def sync_workout_instance_by_id(conn, member_id, workout_instance_id):
    """loads a workout instance from the entity store and upserts it; removes it if it no longer exists"""
    from common.entity_store import EntityStore
    from common.fitness.member_workout_entity import MemberWorkoutInstanceEntity
    wi = EntityStore().get_item(MemberWorkoutInstanceEntity({'member_id': member_id, 'id': workout_instance_id}))
    if wi is None:
        return delete_workout_instance(conn, workout_instance_id)
    return upsert_workout_instance(conn, wi, _load_exercises([wi]))


def rebuild_member_from_entity_store(conn, member_id):
    from common.entity_store import EntityStore
    from common.fitness.member_workout_entity import MemberWorkoutInstanceEntity
    instances = list(EntityStore().list_items(MemberWorkoutInstanceEntity({'member_id': member_id})))
    result = rebuild_member(conn, member_id, instances, _load_exercises(instances))
    with conn:
        conn.execute("INSERT INTO member_build_state (member_id, rebuilt_at) VALUES (?, ?)"
                     " ON CONFLICT(member_id) DO UPDATE SET rebuilt_at = excluded.rebuilt_at", (member_id, _now()))
    return result


def is_member_built(conn, member_id):
    return conn.execute("SELECT 1 FROM member_build_state WHERE member_id = ?", (member_id,)).fetchone() is not None


def ensure_member_built(conn, member_id):
    """the first time a member's history is needed, loads all of it from the entity store. Returns True if it did."""
    if is_member_built(conn, member_id):
        return False
    rebuild_member_from_entity_store(conn, member_id)
    return True


# ---------- hooks for the app: never let a reporting failure break a workout save ----------

def _run_safely(description, fn):
    try:
        conn = connect()
        try:
            return fn(conn)
        finally:
            conn.close()
    except Exception:
        logger.exception(f"exercise analytics db: failed to {description}")
        return None


def on_workout_instance_saved(workout_instance):
    """call after a workout instance is finished or edited. Members not yet built are loaded in full on first view."""
    member_id, wid = workout_instance.get('member_id'), workout_instance.get('id')
    if not member_id or not wid:
        return None
    return _run_safely(f"sync workout instance {wid}",
                       lambda conn: upsert_workout_instance(conn, workout_instance, _load_exercises([workout_instance])))


def on_workout_instance_deleted(workout_instance_id):
    if not workout_instance_id:
        return None
    return _run_safely(f"delete workout instance {workout_instance_id}",
                       lambda conn: delete_workout_instance(conn, workout_instance_id))
