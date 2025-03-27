from common.entity_store import EntityObject

class MemberEntity (EntityObject):
    table_name="MemberTable"
    fields=["id", "name", "level", "short_name", "email", "mobile", "sms_consent"]
    key_field="id"
    partition_value="member"

    def __init__(self, d={}):
        super().__init__(d)        