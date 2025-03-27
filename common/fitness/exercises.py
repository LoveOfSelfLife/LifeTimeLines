from hashlib import sha256
import json
import os

from common.blob_store import BlobStore
from common.entity_store import EntityObject, EntityStore
# from azure.storage.blob import BlobServiceClient, BlobClient

from common.fitness.utils import convert_to_alphanumeric

class ExerciseEntity (EntityObject):
    table_name="ExerciseTable"
    fields=["id", "type", "name", "force", "level", "mechanic", "equipment", "primaryMuscles", "secondaryMuscles", "instructions", "category", "images", "videos"]
    key_field="id"
    partition_value="exercise"

    def __init__(self, d={}):
        super().__init__(d)

class ExerciseIndexEntity (EntityObject):
    table_name="ExerciseIndexTable"
    fields=["exercise_value", "exercise_attribute", "exercises_list" ]
    key_field="exercise_value"
    partition_field="exercise_attribute"

    def __init__(self, d={}):
        super().__init__(d)

def gen_exercise_id(exercise):
    """Generate an exercise id from the exercise name."""
    # run a hash on the exercise json and use that has as part of the id
    hash = sha256()
    hash.update(bytes(json.dumps(exercise), 'utf-8'))
    h = hash.hexdigest()
    alphanum = convert_to_alphanumeric(exercise["name"])
    id = f'{alphanum}-{h[0:16]}'

    return id

    # id = f'{exercise["name"].replace(" ", "-").lower()}-{h}'

    return id

def exercise_generator(exercise_dir):
    """A generator that yields exercises from a directory."""
    for e in os.listdir(exercise_dir):
        exercise_path = f"{exercise_dir}/{e}"
        with open(f"{exercise_path}/exercise.json", 'r') as f:
            exercise = json.load(f)
            exercise["dir"] = e
            exercise["id"] = gen_exercise_id(exercise)
            exercise["images"] = []
            exercise["videos"] = []            
            for img in os.listdir(f"{exercise_path}/images"):
                # upload image to azure blob storage container, and get the url
                # then add the url to the exercise dictionary
                if img == "0.jpg":
                    img_description = "Start"
                elif img == "1.jpg":
                    img_description = "End"
                else:
                    img_description = "<add description>"
                image = { "id": f"{exercise['id']}-{img}", 
                         "description": img_description
                }
                exercise["images"].append(image)

            yield exercise

exercise_attributes = ["primaryMuscles", "secondaryMuscles", "force",  "level",   "mechanic",   "equipment",  "category" ]
# exercie_attributes = ["name", "primaryMuscles", "secondaryMuscles", "equipment", "exerciseType", "mechanicsType", "level", "force", "instructions", "images", "video", "tips", "warnings", "variations", "modifications", "comments", "rating", "ratingCount", "status", "created", "updated"]

def load_exercise_into_index_table(exercise, index_table):
    """Load an exercise into the index table."""
    # Code to load the exercise into the index table goes here
    es = EntityStore()
    for attr in exercise_attributes:
        attr_map = {}
        vals = exercise.get(attr, [])
        # check if vals is a list, then iterate through each items, otherwise just use the item
        if not isinstance(vals, list):
            vals = [vals]

        for val in vals:
            val = val if val else "body"
            # first get the current values from the index table
            ea = es.get_item(ExerciseIndexEntity({"exercise_attribute": attr, "exercise_value": val})) 
            # if the value is not in the index table, then add it
            if not ea:
                es.upsert_item(ExerciseIndexEntity({"exercise_value": val, "exercise_attribute": attr, "exercises_list": [ exercise["name"]]}))
            else:
                # if the value is in the index table, then add the exercise to the list of exercises
                exercises_list = ea.get("exercises_list", [])
                if exercise["name"] not in exercises_list:
                    exercises_list.append(exercise["name"])
                    es.upsert_item(ExerciseIndexEntity({"exercise_value": val, "exercise_attribute": attr, "exercises_list": exercises_list}))  

            #print(f"Exercise: {exercise['name']} has {attr} {val}")

def load_exercises(exercise_dir):
    """Load exercises from a directory into the exercise table."""
    blobstore = BlobStore('fitness-media')
    es = EntityStore()
    for exercise in exercise_generator(exercise_dir):
        exercise_name = exercise["name"]
        for img in exercise["images"]:
            img_id = img["id"]
            src_file = img_id[-5:]
            img_path = f'{exercise_dir}/{exercise["dir"]}/images/{src_file}'
            # blobstore.upload(img_path, img_id)
            print(f"blobstore.upload({img_path}, {img_id})")
        es.upsert_item(ExerciseEntity(exercise))
