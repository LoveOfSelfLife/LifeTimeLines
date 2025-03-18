
from common.entity_store import EntityObject
from common.utils import IDGenerator

class MemberEntity (EntityObject):
    table_name="MemberTable"
    fields=["id", "name", "level", "short_name", "email", "sms", "level" ]
    key_field="id"
    partition_value="member"

    def __init__(self, d={}):
        super().__init__(d)


class ProgramEntity (EntityObject):
    table_name="ProgramTable"
    fields=["id", "type" ]
    key_field="id"
    partition_field="type"

    def __init__(self, d={}):
        super().__init__(d)

