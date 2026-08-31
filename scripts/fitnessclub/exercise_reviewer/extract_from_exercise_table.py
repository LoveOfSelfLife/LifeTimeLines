import os
from dotenv import load_dotenv
import json
from common.entity_store import EntityStore
from common.fitness.exercise_entity import EQUIPMENT, MOVEMENT_CATEGORIES, MUSCLES, PHYSICAL_FITNESS_COMPONENTS, ExerciseEntity
from common.table_store import TableStore
from common.blob_store import BlobStore


def init():
    # load_dotenv('D:/GitHub/DickKemp/LifeTimeLines/test/.env')
    load_dotenv('../.env')
    print(f"Current working directory: {os.getcwd()}")
    TableStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))
    BlobStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))

def map_movements(movements):
    # Implement the mapping logic for movements here
    # create a dict where the key is the movement category and the value is True if present
    movements = {movement: True for movement in movements if movement in MOVEMENT_CATEGORIES}
    
    return movements

def map_muscles(muscles):
    # Implement the mapping logic for muscles here
    muscles = {muscle: True for muscle in muscles if muscle in MUSCLES}
    return muscles

def map_fitness(fitness):
    # Implement the mapping logic for fitness components here
    fitness = {component: True for component in fitness if component in PHYSICAL_FITNESS_COMPONENTS}
    return fitness

def map_equipment(equipment):
    # Implement the mapping logic for equipment here
    new_equipment = {}
    for e in EQUIPMENT:
        if e == equipment:
            new_equipment[e] = True
            return new_equipment
    return new_equipment

def map_custom_attributes(exercise):
    # Implement the mapping logic for custom attributes here
    # setCompletionMeature: reps, time, distance, calories
    # resistance_doubled
    # only_one_set
    # combination?
    custom = {
        "reps" : exercise.get("setCompletionMeasure", None) == "reps",
        "time" : exercise.get("setCompletionMeasure", None) == "time",
        "distance" : exercise.get("setCompletionMeasure", None) == "distance",
        "calories" : exercise.get("setCompletionMeasure", None) == "calories",
        "resistance_doubled" : exercise.get("resistance_doubled", False) == True,
        "only_one_set" : exercise.get("only_one_set", False) == True,
        "combination" : exercise.get("combination", False) == True
    }
    return custom

# def convert_body_only_to_bodyweight():
#     es = EntityStore()
#     exercises = es.list_items(ExerciseEntity())
#     for exercise in exercises:
#         equipment = exercise.get("equipment", None)
#         if equipment and 'body only' in equipment.lower():
#             exercise["equipment"] = "bodyweight"
#             es.upsert_item(ExerciseEntity(exercise))

# def get_equipment():
#     es = EntityStore()
#     normalized_exercises = []
#     equipment_set = set()
#     bodyweight_exercises = set()
#     body_only_exercises = set()
#     exercises = es.list_items(ExerciseEntity())
#     for exercise in exercises:
#         equipment = exercise.get("equipment", None)

#         if equipment:
#             if 'body only' in equipment.lower():
#                 body_only_exercises.add(exercise['name'])
#             if 'bodyweight' in equipment.lower():
#                 bodyweight_exercises.add(exercise['name'])
#             equipment_set.add(equipment)

#     print(f"Number of Bodyweight exercises: {len(bodyweight_exercises)}")
#     print(f"Number of Body Only exercises: {len(body_only_exercises)}")
#     return list(equipment_set)

def extract_exercises():
    es = EntityStore()
    normalized_exercises = []

    exercises = es.list_items(ExerciseEntity())
    for exercise in exercises:
        if exercise.get("hide", False):
            continue
        ex = {}
        ex["id"] = exercise["id"]
        ex["name"] = exercise["name"]
        ex["origin"] = exercise.get("origin", None)
        ex["movements"] = map_movements(exercise.get("movements", {}))
        ex["muscles"] = map_muscles(exercise.get("primaryMuscles", {}))
        ex["fitness"] = map_fitness(exercise.get("physical_fitness_components", {}))
        ex["equipment"] = map_equipment(exercise.get("equipment", None))
        ex["custom"] = map_custom_attributes(exercise)

        if gif := exercise.get("gif", None):
            ex["gif"] = gif
        normalized_exercises.append(ex)

    with open('tbl_store_exercises.json', 'w') as f:
        json.dump([e for e in normalized_exercises], f, indent=4)

if __name__ == '__main__':
    # Initialize the environment and r
    init()
    extract_exercises()
    # print(get_equipment())
    # convert_body_only_to_bodyweight()