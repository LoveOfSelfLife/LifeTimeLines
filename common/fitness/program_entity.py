
from common.entity_store import EntityObject

class ProgramEntity (EntityObject):
    table_name="ProgramTable"
    fields=["id", "type" ]
    key_field="id"
    partition_field="type"

    def __init__(self, d={}):
        super().__init__(d)

