from common.entity_store import EntityObject
from common.utils import IDGenerator

class MemberEntity (EntityObject):
    table_name="MemberTable"
    fields=["id", "name", "sms", "email" ]
    key_field="id"
    partition_value="member"

    def __init__(self, d={}):
        super().__init__(d)


class ExerciseEntity (EntityObject):
    table_name="ExerciseTable"
    fields=["id", "type" ]
    key_field="id"
    partition_field="type"

    def __init__(self, d={}):
        super().__init__(d)

class ProgramEntity (EntityObject):
    table_name="ProgramTable"
    fields=["id", "type" ]
    key_field="id"
    partition_field="type"

    def __init__(self, d={}):
        super().__init__(d)
