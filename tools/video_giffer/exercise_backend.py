"""Azure table/blob access for the v2g tool: exercises list, create exercise, upload gif and link."""
import os
import re
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from common.table_store import TableStore
from common.blob_store import BlobStore
from common.entity_store import EntityStore
from common.utils import generate_id
from common.fitness.exercise_entity import (ExerciseEntity, EQUIPMENT, MUSCLES,
                                            PHYSICAL_FITNESS_COMPONENTS, MOVEMENT_CATEGORIES)

CONN_STR_VAR = "AZURE_STORAGETABLE_CONNECTIONSTRING"
GIF_CONTAINER = "fitness-gifs"
GIF_URI_BASE = "https://ltltablestorage.blob.core.windows.net/" + GIF_CONTAINER
DEFAULT_ORIGIN = "rich"


def _load_env_files():
    """Minimal .env loader (tool dir, then repo root); real environment variables win."""
    for folder in (os.path.dirname(__file__), REPO_ROOT):
        path = os.path.join(folder, ".env")
        if not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def init():
    _load_env_files()
    conn = os.getenv(CONN_STR_VAR)
    if not conn:
        raise RuntimeError(f"{CONN_STR_VAR} is not set (environment variable or .env file).")
    TableStore.initialize(conn)
    BlobStore.initialize(conn)


def get_exercises():
    """Return rows of id, name, gif, origin sorted by name, plus the full entity under 'entity'."""
    es = EntityStore()
    rows = []
    for e in es.list_items(ExerciseEntity()):
        rows.append({
            "id": e.get("id", ""),
            "name": e.get("name", "") or "",
            "gif": e.get("gif", "") or "",
            "origin": e.get("origin", "") or "",
            "entity": e,
        })
    rows.sort(key=lambda r: r["name"].lower())
    return rows


def gif_blob_name(exercise_name):
    slug = re.sub(r"[^a-z0-9]+", "_", exercise_name.lower()).strip("_")
    if not slug:
        raise ValueError("Exercise name produces an empty gif name.")
    return slug + ".gif"


def gif_uri(blob_name):
    return f"{GIF_URI_BASE}/{blob_name}"


def upload_gif_and_link(row, local_gif_path):
    """Upload gif (overwriting any same-named blob) and set the exercise's gif field. Returns the URI."""
    blob_name = gif_blob_name(row["name"])
    store = BlobStore(GIF_CONTAINER)
    with open(local_gif_path, "rb") as data:
        from azure.storage.blob import ContentSettings
        store.get_blob_client(blob_name).upload_blob(
            data, overwrite=True, content_settings=ContentSettings(content_type="image/gif"))
    uri = gif_uri(blob_name)
    entity = row["entity"]
    entity["gif"] = uri
    EntityStore().upsert_item(entity)
    row["gif"] = uri
    return uri


def create_exercise(name, equipment, pfcs, movement_categories, primary_muscles,
                    resistance_doubled=False, origin=DEFAULT_ORIGIN):
    """Create and store a new ExerciseEntity; returns a row dict like get_exercises()."""
    name = name.strip()
    if not name:
        raise ValueError("Name is required.")
    entity = ExerciseEntity({
        "id": generate_id(name),
        "name": name,
        "type": "",
        "equipment_list": list(equipment),
        "physical_fitness_components": list(pfcs),
        "movement_categories": list(movement_categories),
        "primaryMuscles": list(primary_muscles),
        "resistance_doubled": bool(resistance_doubled),
        "origin": origin.strip() or DEFAULT_ORIGIN,
        "udf1": "",
        "udf2": "",
        "gif": "",
        "images": [],
        "videos": [],
        "hide": False,
    })
    EntityStore().upsert_item(entity)
    return {"id": entity["id"], "name": name, "gif": "", "origin": entity["origin"], "entity": entity}
