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

def extract_and_transform_exercises():
    es = EntityStore()
    updated_list = []
    exercises = es.list_items(ExerciseEntity())
    for exercise in exercises:
        
        original_equipment = exercise.get("equipment", None)
        if original_equipment:
            exercise["equipment_list"] = [fixed_equipment(original_equipment)]
        else:
            exercise["equipment_list"] = []
        updated_list.append(ExerciseEntity(exercise))

    es.upsert_items(updated_list)

def fixed_equipment(equipment):
    if equipment == 'e-z curl bar':
        equipment = 'curling_barbell'
    return equipment.replace(" ", "_")

    es.upsert_items(updated_list)
if __name__ == '__main__':
    # Initialize the environment and r
    init()
    extract_and_transform_exercises()

