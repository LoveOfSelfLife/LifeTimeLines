
from common.entity_store import EntityObject

class MemberProgramEntity (EntityObject):
    table_name="MemberProgramTable"
    fields=["id", "member_id", "name", "created_ts", "description", "start_date", "end_date", "assigned_to_member_id"]
    key_field="id"
    partition_field="member_id"

    def __init__(self, d={}):
        super().__init__(d)

class MemberTagsEntity (EntityObject):
    table_name="MemberTagsTable"
    fields=["member_id", 
            "tags"
            ]
    key_field="member_id"
    partition_value="tags"

    def __init__(self, d={}):
        super().__init__(d)
