
import os
from dotenv import load_dotenv
import json
from common.entity_store import EntityStore
from common.fitness.analytics.loader import import_exercise, import_workout
from common.fitness.entities_getter import get_entity
from common.fitness.exercise_entity import ExerciseEntity
from common.fitness.member_workout_entity import  MemberWorkoutInstanceEntity
from common.table_store import TableStore
from common.blob_store import BlobStore
from common.fitness.exercises_loader import load_exercise_into_index_table, exercise_generator, load_exercises

from common.fitness.analytics.schema.create_analytics_sql import create_analytics_views, create_analytics_tables
import sqlite3
import json

DB_PATH = "afc_analytics.sqlite"

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    return conn

def init():
    # load_dotenv('D:/GitHub/DickKemp/LifeTimeLines/test/.env')
    load_dotenv('../../.env')
    print(f"Current working directory: {os.getcwd()}")
    TableStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))
    BlobStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))


def main() -> None:
    conn = get_conn()
    create_analytics_tables(conn)
    init()
    es = EntityStore()
    
    exercise_entities = es.list_items(ExerciseEntity())

    for exercise in exercise_entities:
        import_exercise(conn, exercise)
    
    member_workout_instances = es.list_items(MemberWorkoutInstanceEntity())
    for workout in member_workout_instances:
        import_workout(conn, workout)

    create_analytics_views(conn)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    # main()
    main()

