import os
from dotenv import load_dotenv
import json
from common.entity_store import EntityStore
from common.fitness.entities_getter import get_entity
from common.fitness.exercise_entity import ExerciseEntity
from common.fitness.member_program_entity import MemberProgramsEntity
from common.fitness.member_workout_entity import MemberWorkoutDefinitionEntity, MemberWorkoutInstanceEntity, WorkoutDefinitionEntity
from common.fitness.program_entity import ProgramEntity
from common.fitness.workout_entity import ProgramWorkoutEntity, ProgramWorkoutInstanceEntity, WorkoutEntity
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

    member_programs = es.list_items(MemberProgramsEntity())
    with open('local/member_programs.json', 'w') as f:
        json.dump([mp for mp in member_programs], f, indent=4)

    member_workou_definitions = es.list_items(MemberWorkoutDefinitionEntity())
    with open('local/member_workou_definitions.json', 'w') as f:
        json.dump([mp for mp in member_workou_definitions], f, indent=4)


    member_workout_instances = es.list_items(MemberWorkoutInstanceEntity())
    with open('local/member_workout_instances.json', 'w') as f:
        json.dump([mp for mp in member_workout_instances], f, indent=4)

    programs = es.list_items(ProgramEntity())
    with open('local/programs.json', 'w') as f:
        json.dump([mp for mp in programs], f, indent=4)

    program_workouts = es.list_items(ProgramWorkoutEntity())
    with open('local/program_workouts.json', 'w') as f:
        json.dump([mp for mp in program_workouts], f, indent=4)

    program_workout_instances = es.list_items(ProgramWorkoutInstanceEntity())
    with open('local/program_workout_instances.json', 'w') as f:
        json.dump([mp for mp in program_workout_instances], f, indent=4)


    workout_definitions =  es.list_items(WorkoutDefinitionEntity())
    with open('local/workout_definitions.json', 'w') as f:
        json.dump([mp for mp in workout_definitions], f, indent=4)

    workout_entities = es.list_items(WorkoutEntity())
    with open('local/workout_entities.json', 'w') as f:
        json.dump([mp for mp in workout_entities], f, indent=4)

if __name__ == '__main__':
    # Initialize the environment and r
    init()
    show_tables()
