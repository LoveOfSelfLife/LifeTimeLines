# the csv file missing_gifs_map.csv has 3 columns, exercise id, incorrect blob name, correct blob name
# we should read this csv file, and for each row, retrieve the ExerciseEntity based on the id, then
# update the gif attribute with the correct blob name and save the changes back to the table storage.

import csv
import os

from dotenv import load_dotenv

from common.entity_store import EntityStore
from common.table_store import TableStore
from common.fitness.exercise_entity import ExerciseEntity

load_dotenv('.env')

TableStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))
entity_store = EntityStore()


with open('missing_gifs_map.csv', newline='') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        exercise_id, incorrect_blob_name, correct_blob_name = row
        exercise = entity_store.get_item(ExerciseEntity({'id': exercise_id}))
        if exercise:
            exercise['gif'] = f"https://ltltablestorage.blob.core.windows.net/fitness-vimeo/{correct_blob_name}"
            print(exercise['gif'])
            # print(f"Updating exercise id: {exercise_id} with correct gif: {correct_blob_name}")
            # exercise['gif'] = correct_blob_name
            # entity_store.upsert_item(exercise)
            entity_store.upsert_item(exercise)

