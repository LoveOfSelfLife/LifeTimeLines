import os
from dotenv import load_dotenv
import json
from common.entity_store import EntityStore
from common.entities_getter import get_entity
from common.fitness.exercise_entity import ExerciseEntity
from common.fitness.member_program_entity import MemberProgramsEntity
from common.fitness.member_workout_entity import MemberWorkoutDefinitionEntity, MemberWorkoutInstanceEntity
from common.member_entity import MemberEntity
from common.table_store import TableStore
from common.blob_store import BlobStore
from common.fitness.exercises_loader import load_exercise_into_index_table, exercise_generator, load_exercises
from common.fitness.exercise_entity import ExerciseIndexEntity

def init():
    # load_dotenv('D:/GitHub/DickKemp/LifeTimeLines/test/.env')
    load_dotenv('../.env')
    print(f"Current working directory: {os.getcwd()}")
    TableStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))
    BlobStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))

def show_tables():
    es = EntityStore()
    members = es.list_items(MemberEntity())
    for m in members:
        if m.get('app', None) == 'fitnessclub':
            m['app'] = 'lifetimelines'
            m2 = MemberEntity(m)
            es.upsert_item(m2)

    with open('local/members2.json', 'w') as f:
        json.dump([e for e in members], f, indent=4)
if __name__ == "__main__":
    init()
    show_tables()
