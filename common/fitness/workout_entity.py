
from common.entity_store import EntityObject

class WorkoutEntity (EntityObject):
    table_name="WorkoutTable"
    fields=["id", "name", "sections", "created_ts", "created_by"]
    key_field="id"
    partition_value="workout"

    def __init__(self, d={}):
        super().__init__(d)

class WorkoutInstanceEntity (EntityObject):
    table_name="WorkoutTable"
    fields=["id", "program_id", "name", "sections", "created_ts", "created_by", "done_at_ts"]
    key_field="id"
    partition_field="program_id"

    def __init__(self, d={}):
        super().__init__(d)

