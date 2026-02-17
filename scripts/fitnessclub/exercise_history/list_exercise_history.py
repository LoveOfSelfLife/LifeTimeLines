from datetime import datetime
import os
from dotenv import load_dotenv
import json
from common.entity_store import EntityStore
from common.fitness.member_entity import MemberEntity
from common.fitness.member_exercise_history import MemberExerciseEventHistoryEntity, MemberPerformsExerciseEntity, extract_and_load_exercise_events_from_workout_instance
from common.fitness.member_workout_entity import MemberWorkoutInstanceEntity
from common.table_store import TableStore
from common.blob_store import BlobStore


def init():
    load_dotenv('.env')
    print(f"Current working directory: {os.getcwd()}")
    TableStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))
    BlobStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))

def list_exercise_history():
    member_id = ''
    es = EntityStore()
    members = list(es.list_items(MemberEntity()))
    for member in members:
        member_id = member.get('id', None)
        member_performes_exercise_entities = list(es.list_items(MemberPerformsExerciseEntity({'member_id': member_id})))
        for mpe in member_performes_exercise_entities:
            #print(f"Member ID: {member_id}, Exercise Instance Partition Key: {mpe.get('exercise_instance_partition_key', None)}")
            exercise_history = list(es.list_items(MemberExerciseEventHistoryEntity({'exercise_instance_partition_key': mpe.get('exercise_instance_partition_key', None)})))
            for event in exercise_history:
                #print(f"    Event ID: {event.get('event_id', None)}, Exercise Instance Partition Key: {event.get('exercise_instance_partition_key', None)}, Member ID: {event.get('member_id', None)}, Member Workout Instance ID: {event.get('member_workout_instance_id', None)}, Member Program Instance ID: {event.get('member_program_instance_id', None)}, Date Time: {event.get('date_time', None)}, Sets: {event.get('sets', None)}, Reps: {event.get('reps', None)}, Weight: {event.get('weight', None)}, Weight Unit: {event.get('weight_unit', None)}, Time: {event.get('time', None)}, Tempo: {event.get('tempo', None)}")
                print(f"Exercise ID: {event.get('exercise_id', None)}, Member ID: {event.get('member_id', None)}, Date Time: {event.get('date_time', None)}, Sets: {event.get('sets', None)}, Reps: {event.get('reps', None)}, Weight: {event.get('weight', None)}, Weight Unit: {event.get('weight_unit', None)}")

if __name__ == '__main__':
    # Initialize the environment and r
    init()
    list_exercise_history()
