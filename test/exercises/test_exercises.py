
import os
from dotenv import load_dotenv
import unittest
import json
from common.entity_store import EntityStore
from common.table_store import TableStore
from common.blob_store import BlobStore
from services.fitnessclub.exercises import load_exercise_into_index_table, exercise_generator, load_exercises
from services.fitnessclub.exercises import ExerciseEntity, ExerciseIndexEntity

class TestExercises(unittest.TestCase):

    def setUp(self) -> None:
        print(f"setUp()")
        load_dotenv('D:/GitHub/DickKemp/LifeTimeLines/test/.env')
        print(f"{os.getcwd()}")
        print( f"{os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING')}")
        TableStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))
        BlobStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))
        return super().setUp()
    
    def test_gen_exercise_json(self):
        print(f"test_gen_exercise_json()")
        exercise_dir = "d:/github/Dickkemp/exercises.json/exercises"
        return
        with open("d:/github/Dickkemp/LifeTimeLines/exercises.json", 'w') as f:
            f.write('[\n')
            for exercise in exercise_generator(exercise_dir):
                print(f"Exercise: {exercise['name']}")
                f.write(json.dumps(exercise))
                f.write(",\n")
                # load_exercise_into_index_table(exercise, "ExerciseIndexTable")
            f.write(']\n')

    def test_load_exercise_store(self):
        print(f"load_exercise_store")
        exercise_dir = "d:/github/Dickkemp/exercises.json/exercises"
        for exercise in exercise_generator(exercise_dir):       
            print(f"Exercise: {json.dumps(exercise, indent=4)}")
            break
            # image
        load_exercises(exercise_dir)

    def test_read_exercises_table(self):
        print(f"read_exercises_table")
        es = EntityStore()
        for e in es.list_items(ExerciseEntity()):
            print(f"Exercise: {e}")
        

    # def test_gen_index(self):
    #     exercise_dir = "d:/github/Dickkemp/exercises.json/exercises"
    #     exercises_list = list(exercise_generator(exercise_dir))
    #     exercise_index_values1_index_tables(exercise_index_values1)
    #     print(index1)
    #     index2 = update_exercise_index_tables(exercise_index_values2)
    #     print(index2)

    #     r = update_exercise_index_tables(exercise_index_values)


if __name__ == '__main__':
    unittest.main()
