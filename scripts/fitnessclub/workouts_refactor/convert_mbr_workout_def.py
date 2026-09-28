import os
from dotenv import load_dotenv
import json
from common.entity_store import EntityObject, EntityStore
from common.fitness.member_workout_entity import MemberWorkoutDefinitionEntity

from common.table_store import TableStore
from common.blob_store import BlobStore

class ConvertedMemberWorkoutDefinitionEntity (EntityObject):
    table_name="MemberWorkoutDefinitionTable"
    fields=["id", 
            "name", 
            "description", 
            "workout_sections", 
            "created_ts", 
            "created_by", 
            "assigned_to_member_id",    # references the member to whom this workout is assigned
            "tags",                     # list of tags associated with the workout
            "member_program_id",        # reference the member program this workout is part of, if any
            "order_index",              # index to determine the order of workouts within a program
            "purpose",                  # optional field to describe the purpose of this workout within the context of a program
            "workout_type"              # type of workout: "standard" (default) or "alternative"
            ]
    key_field="id"
    partition_value="workout"

    def __init__(self, d={}):
        super().__init__(d)

def init():
    load_dotenv('../.env')
    print(f"Current working directory: {os.getcwd()}")
    TableStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))
    BlobStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))

def get_workouts(es):
    programs = []
    for program in es.list_items(MemberWorkoutDefinitionEntity()):
        programs.append(program)
    return programs

def convert_workouts(programs):
    print(f"Found {len(programs)} programs to migrate")
    converted = []
    for p in programs:
        print('.', end='', flush=True)
        updated_pg = ConvertedMemberWorkoutDefinitionEntity(p)
        converted.append(updated_pg)
    return converted

def store_entities(entities, entity_class):
    es = EntityStore()
    for entity in entities:
        es.upsert_item(entity_class(entity))

if __name__ == '__main__':
    init()
    es = EntityStore()
    programs = get_workouts(es)
    converted_programs = convert_workouts(programs)
    store_entities(converted_programs, ConvertedMemberWorkoutDefinitionEntity)
