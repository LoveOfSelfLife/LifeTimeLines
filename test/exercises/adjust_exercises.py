
import os
from dotenv import load_dotenv
import json
from common.entity_store import EntityStore
from common.table_store import TableStore
from common.blob_store import BlobStore
from common.fitness.exercises import load_exercise_into_index_table, exercise_generator, load_exercises
from common.fitness.exercises import ExerciseEntity, ExerciseIndexEntity


def init():
    # load_dotenv('D:/GitHub/DickKemp/LifeTimeLines/test/.env')
    load_dotenv('../.env')
    print(f"{os.getcwd()}")
    print( f"{os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING')}")
    TableStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))
    BlobStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))

def read_exercises_table():
        print(f"read_exercises_table")
        es = EntityStore()
        exercises = []
        for e in es.list_items(ExerciseEntity()):
            exercises.append(e)
        print(f"number of exercises: {len(exercises)}")
        max_show = 4
        for exercise in exercises:
            if max_show == 0:
                break
            max_show -= 1
            print(f"exercise: {json.dumps(exercise, indent=4)}")

def transform_exercise_table():
    es = EntityStore()
    exercises = []
    for e in es.list_items(ExerciseEntity()):
        exercises.append(e)
    print(f"number of exercises: {len(exercises)}")
    updated_exercises = []
    for exercise in exercises:
        # Transform the exercise data as needed
        transformed_exercise = transform_exercise(exercise)
        updated_exercises.append(transformed_exercise)
    es.upsert_items(updated_exercises, ExerciseEntity())

def export_exercises():
    es = EntityStore()
    exercises = []
    for e in es.list_items(ExerciseEntity()):
        exercises.append(e)

    updated_exercises = []
    for exercise in exercises:
        # Transform the exercise data as needed
        transformed_exercise = transform_exercise(exercise)
        updated_exercises.append(transformed_exercise)

    json_file = "exercise_export.json"
    with open(json_file, "w") as f:
        json.dump(updated_exercises, fp=f, indent=4)


def transform_exercise(exercise_data):
    # Transform the exercise data as needed
    # For example, let's just return the exercise as is for now
    exercise = exercise_data.copy()
    if exercise.get("images") is None:
        exercise["images"] = []
    for img in exercise["images"]:
        # replace space with a dash in the image name
        img['type'] = img['description'].replace(" ", "-").lower()
        img['description'] = f"{img['description']}"
    if exercise.get("videos") is None:
        exercise["videos"] = []
    exercise['equipment_number'] = ""
    exercise['origin'] = "exercises.json"
    return exercise 


if __name__ == '__main__':
    # Initialize the environment and run the test function
    init()
    # read_exercises_table()
    export_exercises()
