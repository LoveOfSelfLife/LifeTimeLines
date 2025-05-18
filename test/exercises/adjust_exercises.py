
import os
from dotenv import load_dotenv
import json
from common.entity_store import EntityStore
from common.fitness.exercise_entity import ExerciseEntity
from common.table_store import TableStore
from common.blob_store import BlobStore
from common.fitness.exercises_loader import load_exercise_into_index_table, exercise_generator, load_exercises
from common.fitness.exercise_entity import ExerciseIndexEntity


def init():
    # load_dotenv('D:/GitHub/DickKemp/LifeTimeLines/test/.env')
    load_dotenv('../.env')
    print(f"{os.getcwd()}")
    print( f"{os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING')}")
    TableStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))
    BlobStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))

def transform_exercise_table(f):
    es = EntityStore()
    exercises = []
    for e in es.list_items(ExerciseEntity()):
        exercises.append(e)
    print(f"number of exercises: {len(exercises)}")
    updated_exercises = []
    for exercise in exercises:
        # Transform the exercise data as needed
        transformed_exercise = ExerciseEntity(f(exercise))
        updated_exercises.append(transformed_exercise)
    es.upsert_items(updated_exercises)

def export_exercises(json_file = "exercise_export.json"):
    es = EntityStore()
    exercises = []
    for e in es.list_items(ExerciseEntity()):
        exercises.append(e)

    updated_exercises = []
    for exercise in exercises:
        updated_exercises.append(exercise)
    
    with open(json_file, "w") as f:
        json.dump(updated_exercises, fp=f, indent=4)

def transform_instructions(exercise_data):
    # Transform the exercise instructions from a list of strings into a single string delimited by new lines
    exercise = exercise_data.copy()
    if exercise.get("instructions", None) is None:
        exercise["instructons"] = ""
    if isinstance(exercise["instructions"], list):
        exercise["instructions"] = "\n".join(exercise["instructions"])
    exercise['setCompletionMeasure'] = "reps"
    return exercise 

def convert_image_id_to_url(exercise_data):
    # Transform the exercise instructions from a list of strings into a single string delimited by new lines
    exercise = exercise_data.copy()
    base_url = "https://ltltablestorage.blob.core.windows.net/fitness-media"
    if exercise.get("images", None) is None:
        exercise["images"] = []
    else:
        for img in exercise["images"]:
            if 'id' not in img:
                continue
            img['url'] = f"{base_url}/{img['id']}"
            del img['id']  # remove the id field
    return exercise 

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
    exercise['equipment_detail'] = ""
    exercise['origin'] = "exercises.json"
    return exercise 


if __name__ == '__main__':
    # Initialize the environment and run the test function
    init()
    # read_exercises_table()
    # transform_exercise_instructions()
    # check_exercise_instructions()
    # transform_exercise_table(transform_add_setcompletionmeasure)
    # export_exercises()
    # transform_exercise_table(convert_image_id_to_url)
    export_exercises("exercise_export_20250516.json")
    