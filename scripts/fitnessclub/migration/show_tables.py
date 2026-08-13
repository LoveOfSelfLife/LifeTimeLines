import os
from dotenv import load_dotenv
import json
from common.entity_store import EntityStore
from common.fitness.entities_getter import get_entity
from common.fitness.exercise_entity import ExerciseEntity
from common.fitness.member_program_entity import MemberProgramsEntity
from common.fitness.member_workout_entity import MemberWorkoutDefinitionEntity, MemberWorkoutInstanceEntity
from common.table_store import TableStore
from common.blob_store import BlobStore
from common.fitness.exercises_loader import load_exercise_into_index_table, exercise_generator, load_exercises
from common.fitness.exercise_entity import ExerciseIndexEntity


def init():
    # load_dotenv('D:/GitHub/DickKemp/LifeTimeLines/test/.env')
    load_dotenv('.env')
    print(f"Current working directory: {os.getcwd()}")
    TableStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))
    BlobStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))

def show_tables():
    es = EntityStore()

    exercises = es.list_items(ExerciseEntity())
    with open('local/exercises.json', 'w') as f:
        json.dump([e for e in exercises], f, indent=4)

    member_programs = es.list_items(MemberProgramsEntity())
    with open('local/member_programs.json', 'w') as f:
        json.dump([mp for mp in member_programs], f, indent=4)

    member_workou_definitions = es.list_items(MemberWorkoutDefinitionEntity())
    with open('local/member_workout_definitions.json', 'w') as f:
        json.dump([mp for mp in member_workou_definitions], f, indent=4)

    member_workout_instances = es.list_items(MemberWorkoutInstanceEntity())
    with open('local/member_workout_instances.json', 'w') as f:
        json.dump([mp for mp in member_workout_instances], f, indent=4)

if __name__ == '__main__':
    # Initialize the environment and r
    init()
    show_tables()
