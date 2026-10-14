# this script will get all exercise entity objects from azure table storage, and if the exercise has 
# a value for the gif attribute, it will display the exercise name and the gif attribute value
from urllib.parse import urlparse

from dotenv import load_dotenv

from common import blob_store
from common.blob_store import BlobStore
from common.entity_store import EntityStore
from common.table_store import TableStore
from common.fitness.exercise_entity import ExerciseEntity
load_dotenv('.env')

import os

def init():
    # load_dotenv('D:/GitHub/DickKemp/LifeTimeLines/test/.env')
    load_dotenv('../.env')
    TableStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))
    BlobStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))

def get_names():
    es = EntityStore()
    exercises = es.list_items(ExerciseEntity())

    for exercise in exercises:
        if exercise.get('gif', None):
            blob_uri = exercise.get('gif')
            # print('.', end='', flush=True)
            # print(f"Exercise Name: {exercise.get('name', None)}, GIF: {exercise.get('gif', None)}")
            try:
                    # 1. Parse the URI to extract container and blob paths
                    parsed_url = urlparse(blob_uri)
                    
                    # path looks like "/container-name/folder/file.txt"
                    path_parts = parsed_url.path.lstrip('/').split('/', 1)
                    
                    if len(path_parts) < 2:
                        raise ValueError("Invalid Blob URI format. Missing container or blob name.")
                        
                    container_name = path_parts[0]
                    blob_name = path_parts[1]
                    # print(f"Exercise Name: {exercise.get('name', None)}, Container: {container_name}, Blob: {blob_name}")
                    if not blob_store.BlobStore(container_name).blob_exists(blob_name):
                        # print(f"Blob '{blob_name}' does not exist in container '{container_name}'")
                        print(f"exercise id: {exercise.get('id', None)}: Blob '{blob_name}' does not exist in container '{container_name}'")    
            except Exception as e:
                print(f"ERROR:{exercise.get('name', None)} : '{blob_uri}': {e}")

if __name__ == "__main__":
    init()
    get_names()
