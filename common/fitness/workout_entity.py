
from common.entity_store import EntityObject

class WorkoutEntity (EntityObject):
    table_name="WorkoutTable"
    fields=["id", "name", "sections", "created_ts", "created_by"]
    key_field="id"
    partition_value="workout"

    def __init__(self, d={}):
        super().__init__(d)

