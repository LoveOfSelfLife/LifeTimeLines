
import os
import uuid
from dotenv import load_dotenv
import json
from common.entity_store import EntityStore
# from common.fitness.exercise_entity import ExerciseEntity, ExerciseEntityBackup, ExerciseReviewEntity
from common.fitness.workout_entity import WorkoutEntity, WorkoutInstanceEntity
from common.table_store import TableStore
from common.blob_store import BlobStore
from common.fitness.exercises_loader import load_exercise_into_index_table, exercise_generator, load_exercises
from common.fitness.exercise_entity import ExerciseIndexEntity


def init():
    load_dotenv('../.env')
    TableStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))
    BlobStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))

    
        
def workouts1():
    es = EntityStore()
    workout_entity = WorkoutEntity()
    
    workouts = list(es.list_items2(workout_entity))
    print(f"number of workouts: {len(workouts)}")
    # for workout in workouts:
    #     print(workout)
    id  = 'bee01423-5767-4424-a3da-8bd8e462b295'    
    workout = es.get_item(WorkoutEntity({"id": id}))
    print(f"workout: {workout}")
    # do a deep copy of the workout
    new_workout = workout.copy()
    workout['id'] = "copy-" + str(uuid.uuid4())
    
    es.upsert_item(WorkoutEntity(new_workout))

    workouts = list(es.list_items2(workout_instance_entity2, dfilter=[]))

    workouts = list(es.list_items2(workout_instance_entity, dfilter=[]))
    print(f"number of workouts: {len(workouts)}")
    # for workout in workouts:
    #     print(workout)

    workout_instance_entity2 = WorkoutInstanceEntity({"member_id": "43f641cc-9aea-410a-86a2-0a9256ce9188",})
    workouts = list(es.list_items2(workout_instance_entity2, dfilter=[]))
    print(f"number of workouts: {len(workouts)}")
    # for workout in workouts:
    #     print(workout)

    workout_instance_entity3 = WorkoutInstanceEntity({"member_id": "workout",})
    workouts = list(es.list_items2(workout_instance_entity3, dfilter=[]))
    print(f"number of workouts: {len(workouts)}")
    # for workout in workouts:
    #     print(workout)


if __name__ == '__main__':
    # Initialize the environment 
    init()
    print("Starting workouts experiment..........................................................................................")
    workouts1()
