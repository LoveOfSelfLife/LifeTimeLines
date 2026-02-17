from datetime import datetime
import os
from dotenv import load_dotenv
import json
from common.entity_store import EntityStore
from common.fitness.member_exercise_history import extract_and_load_exercise_events_from_workout_instance
from common.fitness.member_workout_entity import MemberWorkoutInstanceEntity
from common.table_store import TableStore
from common.blob_store import BlobStore


def init():

    load_dotenv('.env')
    print(f"Current working directory: {os.getcwd()}")
    TableStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))
    BlobStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))

def test_migration():
    member_id = ''
    es = EntityStore()
    workout_instances = list(es.list_items(MemberWorkoutInstanceEntity()))
    print(f"Total workout instances to process: {len(workout_instances)}")
    for workout_instance in workout_instances:
        # print(workout_instance.get('id', None) )
        started_ts = workout_instance.get('started_ts', None)
        started_date = started_ts.split('T')[0] if started_ts else 'unknown_date'
        # started_ts is in this format: '2025-08-25T15:42:16.547008', we want to convert it to this format: '03:42 PM'
        started_time_in_AM_PM = datetime.strptime(started_ts, '%Y-%m-%dT%H:%M:%S.%f').strftime('%I:%M %p') if started_ts else 'unknown_time'
        #print(f"Processing workout instance with ID: {workout_instance.get('id', None)}, started_date: {started_date}, started_time: {started_time_in_AM_PM}")
        extract_and_load_exercise_events_from_workout_instance(workout_instance)

if __name__ == '__main__':
    # Initialize the environment and r
    init()
    test_migration()
