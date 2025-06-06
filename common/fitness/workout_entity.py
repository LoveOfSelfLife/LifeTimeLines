
from common.entity_store import EntityObject

class WorkoutEntity (EntityObject):
    table_name="WorkoutTable"
    fields=["id", "name", "sections", "created_ts", "created_by"]
    key_field="id"
    partition_value="workout"

    def __init__(self, d={}):
        super().__init__(d)

class ProgramWorkoutEntity (EntityObject):
    table_name="ProgramWorkoutTable"
    fields=["id", "name", "sections", "created_ts", "created_by", "program_id", "parent_workout_id"]
    key_field="id"
    partition_field="program_id"

    def __init__(self, d={}):
        super().__init__(d)

class WorkoutInstanceEntity (EntityObject):
    table_name="MemberWorkoutTable"
    fields=["id", "member_id", "name", "sections", "created_ts", "created_by", "done_at_ts"]
    key_field="id"
    partition_field="member_id"

    def __init__(self, d={}):
        super().__init__(d)

