import os
from dotenv import load_dotenv
import json
from common.entity_store import EntityStore
from common.fitness.exercise_entity import EQUIPMENT, MOVEMENT_CATEGORIES, MUSCLES, PHYSICAL_FITNESS_COMPONENTS, ExerciseEntity
from common.table_store import TableStore
from common.blob_store import BlobStore
from scripts.fitnessclub.ace.load_exercises import store_exercises


def init():
    # load_dotenv('D:/GitHub/DickKemp/LifeTimeLines/test/.env')
    load_dotenv('../.env')
    print(f"Current working directory: {os.getcwd()}")
    TableStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))
    BlobStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))

def load_exercises_from_json(file_path):
    with open(file_path, 'r') as f:
        exercises = json.load(f)
    return exercises

def standardize_exercises(exercises):
    std_exercises = []
    """
    "id", 
    "type", 
    "name", 
    "force", 
    "level", 
    "mechanic", 
    "equipment_list",
    "origin",  
    "primaryMuscles", 
    "secondaryMuscles", 
    "instructions", 
    "category", 
    "images", 
    "videos", 
    "gif",
    "created_by_member_id", 
    "setCompletionMeasure", 
    "resistance_doubled", # has a boolean value
    "only_one_set", # has a boolean value
    "udf1", "udf2", 
    "physical_fitness_components", 
    "movement_categories", 
    "hide"
    """
    for exercise in exercises:
        ex = {}
        ex["id"] = f'{exercise["id"]}_vimeo'
        if name := gen_name(exercise["id"]):
            ex["name"] = name
        else:
            print(f"Exercise with id {exercise['id']} is excluded from renaming.")
            continue
        ex["origin"] = "vimeo"
        ex["physical_fitness_components"] = gen_pfc(exercise.get("fitness", []))
        ex["movement_categories"] = gen_mc(exercise.get("movements", []))
        ex["equipment_list"] = gen_equipment(exercise.get("equipment", []))
        ex["setCompletionMeasure"] = gen_scm(exercise.get("custom", {}))
        ex["primaryMuscles"] = gen_muscles(exercise.get("muscles", []))
        ex["only_one_set"] = gen_only_one_set(exercise.get("custom", {}))
        ex["resistance_doubled"] = gen_resistance_doubled(exercise.get("custom", {}))
        ex["gif"] = gen_gif(exercise)
        std_exercises.append(ExerciseEntity(ex))
    return std_exercises

def gen_scm(custom_dict):
    if custom_dict.get("reps", False):
        return "reps"
    if custom_dict.get("time", False):
        return "time"
    if custom_dict.get("distance", False):
        return "distance"
    if custom_dict.get("calories", False):
        return "calories"
    return None
def gen_only_one_set(custom_dict):
    if custom_dict.get("only_one_set", False):
        return "on"
    return None

def gen_resistance_doubled(custom_dict):
    if custom_dict.get("resistance_doubled", False):
        return "on"
    return None

def gen_name(id):
    # Implement the logic to standardize the exercise name
    # read the csv file called "v2.csv"
    # the first column is the exercise id, second column is the new name, if the 3rd column has the value "no"
    # then we exclude that exercise from being renamed - we return None for that name
    import csv
    with open("v2.csv", newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if row[0] == id:
                if len(row) > 2 and row[2].lower() == "no":
                    return None
                name = row[1]
                return name
    return None

def gen_equipment(equip_dict):
    # Implement the logic to standardize the equipment list
    list_of_equipment = []
    for k,v in equip_dict.items():
        if v:
            list_of_equipment.append(k)
    return list_of_equipment
def gen_pfc(fitness_dict):
    # Implement the logic to standardize the physical fitness components
    list_of_pfc = []
    for k,v in fitness_dict.items():
        if v:
            list_of_pfc.append(k)
    return list_of_pfc
def gen_mc(movements_dict):
    # Implement the logic to standardize the movement categories
    list_of_mc = []
    for k,v in movements_dict.items():
        if v:
            list_of_mc.append(k)
    return list_of_mc

def gen_gif(exercise):
    # Implement the logic to get the gif URL or path for the exercise
    id = exercise.get("id")
    return f"https://ltltablestorage.blob.core.windows.net/fitness-vimeo/{id}.gif"

def gen_muscles(muscles_dict):
    list_of_muscles = [k for k,v in muscles_dict.items() if v]
    return list_of_muscles

def store_exercises(exercises):
    es = EntityStore()
    es.upsert_items(exercises)
    print(f"Stored {len(exercises)} exercises.")  

if __name__ == '__main__':
    # Initialize the environment
    init()
    exercises = load_exercises_from_json('vimeo_exercises.json')
    std_exercises = standardize_exercises(exercises)
    with open('std_vimeo_xercises.json', 'w') as f:
        json.dump([e for e in std_exercises], f, indent=4)
    store_exercises(std_exercises)
