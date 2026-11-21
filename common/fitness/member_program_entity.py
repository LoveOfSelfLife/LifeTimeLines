
from common.entity_store import EntityObject
from common.fitness.fitness_presentation import assigned_client_name, member_name, program_image

# class MemberProgramEntity (EntityObject):
#     table_name="MemberProgramTable"
#     fields=["id", "member_id", "name", "created_ts", "description", "start_date", "end_date", "assigned_to_member_id"]
#     key_field="id"
#     partition_field="member_id"

#     def __init__(self, d={}):
#         super().__init__(d)

class MemberProgramsEntity (EntityObject):
    table_name="MemberProgramsTable"
    fields=["id", "name", "created_by", "created_ts", "description", "start_date", "end_date", "assigned_to_member_id",
            "objective_ids"]   # ids of the program objectives this program is measured against
    key_field="id"
    partition_value="programs"
    list_presentation = (
        {"label": "name", "value": lambda entity: entity.get("name")},
        {"label": "start", "value": lambda entity: entity.get("start_date", "")},
        {"label": "end", "value": lambda entity: entity.get("end_date", "")},
        {"label": "client", "value": assigned_client_name},
    )
    card_presentation = {
        "title": lambda entity: entity.get("name", ""),
        "image": program_image,
        "fields": (
            {"label": "Start", "value": lambda entity: entity.get("start_date")},
            {"label": "End", "value": lambda entity: entity.get("end_date")},
            {"label": "Client", "value": member_name},
        ),
        "actions": ("edit", "analyze"),
    }

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
