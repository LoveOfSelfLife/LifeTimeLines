
from common.entity_store import EntityObject
from common.fitness.program_schema import program_schema

class ProgramEntity (EntityObject):
    table_name="ProgramTable"
    fields=["id", "member_id", "name", "description", "start_date", "end_date", "workouts" ]
    key_field="id"
    partition_field="member_id"
    schema=program_schema

    def __init__(self, d={}):
        super().__init__(d)

