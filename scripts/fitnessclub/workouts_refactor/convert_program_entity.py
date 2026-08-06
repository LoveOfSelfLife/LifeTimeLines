import os
from dotenv import load_dotenv
import json
from common.entity_store import EntityStore
from common.fitness.member_program_entity import MemberProgramEntity, MemberProgramsEntity

from common.table_store import TableStore
from common.blob_store import BlobStore


def init():
    load_dotenv('../.env')
    print(f"Current working directory: {os.getcwd()}")
    TableStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))
    BlobStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))

def get_programs(es):
    programs = []
    for program in es.list_items(MemberProgramEntity()):
        programs.append(program)
    return programs

def convert_programs(programs):
    print(f"Found {len(programs)} programs to migrate")
    converted_programs = []
    for p in programs:
        print('.', end='', flush=True)
        updated_pg = MemberProgramsEntity(p)
        updated_pg['created_by'] = p.get('member_id')
        updated_pg['created_ts'] = p.get('created_ts', p.get('Timestamp'))
        converted_programs.append(updated_pg)
    return converted_programs

def store_entities(entities, entity_class):
    es = EntityStore()
    for entity in entities:
        es.upsert_item(entity_class(entity))

if __name__ == '__main__':
    init()
    es = EntityStore()
    programs = get_programs(es)
    converted_programs = convert_programs(programs)
    store_entities(converted_programs, MemberProgramsEntity)
