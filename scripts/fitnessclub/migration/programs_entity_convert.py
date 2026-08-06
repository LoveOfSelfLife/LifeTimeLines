import os
from dotenv import load_dotenv
import json
from common.entity_store import EntityStore
from common.fitness.member_program_entity import MemberProgramEntity
from common.fitness.member_workout_entity import MemberWorkoutDefinitionEntity, MemberWorkoutInstanceEntity, WorkoutDefinitionEntity
from common.table_store import TableStore
from common.blob_store import BlobStore



from common.entity_store import EntityObject
from common.fitness.entities_getter import get_entity
from common.fitness.hx_common import hx_render_template


class WorkoutDefinitionBackupEntity (WorkoutDefinitionEntity):
    table_name="WorkoutDefinitionBackupTable"

    def __init__(self, d={}):
        super().__init__(d)

class MemberWorkoutDefinitionBackupEntity (MemberWorkoutDefinitionEntity):
    table_name="MemberWorkoutDefinitionBackupTable"

    def __init__(self, d={}):
        super().__init__(d)

class MemberWorkoutInstanceBackupEntity (MemberWorkoutInstanceEntity):
    table_name="MemberWorkoutInstanceBackupTable"

    def __init__(self, d={}):
        super().__init__(d)

def init():
    # load_dotenv('D:/GitHub/DickKemp/LifeTimeLines/test/.env')
    load_dotenv('.env')
    print(f"Current working directory: {os.getcwd()}")
    TableStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))
    BlobStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))

def get_programs(es):
    programs = []
    for program in es.list_items(MemberProgramEntity()):
        programs.append(program)
    return programs

def convert_programs():
    es = EntityStore()
    programs = get_programs(es)
    print(f"Found {len(programs)} programs to migrate")
    for p in programs:
        print('.', end='', flush=True)
        updated_pg  = convert_program(p)
        es.upsert_item(updated_pg)

def convert_program(program):
    if program.get('assigned_to_member_id') is None:
        program['assigned_to_member_id'] = program.get('member_id')
    return program

if __name__ == '__main__':
    init()
    convert_programs() 
