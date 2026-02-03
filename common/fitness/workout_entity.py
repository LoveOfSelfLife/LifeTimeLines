
from common.entity_store import EntityObject

# class WorkoutEntity (EntityObject):
#     table_name="WorkoutTable"
#     # type is used to differentiate between full workouts vs partial workouts that are specific to one section, e.g. warmups or core workouts
#     # type is set to "full" for full workouts, and "section" for section-specific workouts
#     # default is "full"
#     fields=["id", "name", "sections", "created_ts", "created_by", "type"]
#     key_field="id"
#     partition_value="workout"

#     def __init__(self, d={}):
#         super().__init__(d)

# class ProgramWorkoutEntity (EntityObject):
#     table_name="ProgramWorkoutTable"
#     fields=["id", "name", "sections", "created_ts", "created_by", "program_id", "parent_workout_id"]
#     key_field="id"
#     partition_field="program_id"

#     def __init__(self, d={}):
#         super().__init__(d)

# class ProgramWorkoutInstanceEntity (EntityObject):
#     table_name="ProgramWorkoutInstanceTable"
#     fields=["id", "program_workout_id", "name", "sections"]
#     key_field="id"
#     partition_field="program_workout_id"

#     def __init__(self, d={}):
#         super().__init__(d)



