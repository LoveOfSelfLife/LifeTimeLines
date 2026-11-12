'''
this script updates the movement categories for exercises in the exercise history.
- if an exercise has any one of "CORE-AE", "CORE-AF", "CORE-AR", "CORE-HF", "CORE-ROT", then this will imply that "CORE" is also in the list, even if "CORE" is not explicitly in the list.  That is, it is "implied" by the presence of any one of the other values.
- this will ensure that the broader category is included whenever a more specific subcategory is present.
- similarly:
    - "SQUAT-ASYM", "SQUAT-SL" or "SQUAT-SYM" imply "SQUAT"
    - "PULL-VERT" or "PULL-HORZ" will imply "PULL"
    - "PUSH-VERT" or "PUSH-HORZ" will imply "PUSH"
    - "HINGE-BRIDGE", "HINGE-SL" or "HINGE-SYM" will imply "HINGE"

Script will loop through all exerciseEntity instances and update their movement categories accordingly.
'''

from datetime import datetime
import os
from dotenv import load_dotenv
import json
from common.entity_store import EntityStore
from common.fitness.exercise_entity import ExerciseEntity
from common.table_store import TableStore



def init():
    load_dotenv('.env')
    print(f"Current working directory: {os.getcwd()}")
    TableStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))

def update_exercise_movement_categories(exercise):
    movement_categories = set(exercise.get("movement_categories", []))

    if any(cat in movement_categories for cat in ["CORE-AE", "CORE-AF", "CORE-AR", "CORE-HF", "CORE-ROT"]):
        movement_categories.add("CORE")
    if any(cat in movement_categories for cat in ["SQUAT-ASYM", "SQUAT-SL", "SQUAT-SYM"]):
        movement_categories.add("SQUAT")
    if any(cat in movement_categories for cat in ["PULL-VERT", "PULL-HORZ"]):
        movement_categories.add("PULL")
    if any(cat in movement_categories for cat in ["PUSH-VERT", "PUSH-HORZ"]):
        movement_categories.add("PUSH")
    if any(cat in movement_categories for cat in ["HINGE-BRIDGE", "HINGE-SL", "HINGE-SYM"]):
        movement_categories.add("HINGE")

    exercise["movement_categories"] = list(movement_categories)

def main():
    init()
    entity_store = EntityStore()
    all_exercises = entity_store.list_items(ExerciseEntity())
    updated_exercises = []
    for exercise in all_exercises:
        update_exercise_movement_categories(exercise)
        updated_exercises.append(exercise)
    entity_store.upsert_items(updated_exercises)

if __name__ == "__main__":
    main()

