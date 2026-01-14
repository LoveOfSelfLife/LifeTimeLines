from dotenv import load_dotenv
from common.entity_store import EntityStore, EntityObject
from common.fitness.exercise_entity import ExerciseEntity, ExerciseIndexEntity
from common.table_store import TableStore
import os
if __name__ == "__main__":
    print(f"setUp()")
    load_dotenv('../.env')
    print(f"{os.getcwd()}")
    print( f"{os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING')}")
    TableStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))    

    # Create an instance of EntityStore
    entity_store = EntityStore()

    # Create an instance of ExerciseEntity and ExerciseIndexEntity
    exercise_entity = ExerciseEntity()
    exercise_index_entity = ExerciseIndexEntity()

    # List items in the ExerciseEntity table
    exercise_items = entity_store.list_items(exercise_entity)
    print("Exercise Items:")
    for item in exercise_items:
        print(item)
        break

    # List items in the ExerciseIndexEntity table
    exercise_index_items = entity_store.list_items(exercise_index_entity)
    print("\nExercise Index Items:")
    for item in exercise_index_items:
        print(item)
        break

    for k,v in EntityObject.entity_name_to_entity_class_map.items():
        print(f"item: {k}")
        print(f"entity_class: {v}")
        



        