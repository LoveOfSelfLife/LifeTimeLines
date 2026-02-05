from common.entity_store import EntityObject
from common.fitness.entities_getter import get_entity


class WorkoutDefinitionEntity (EntityObject):
    table_name="WorkoutDefinitionTable"
    # type is used to differentiate between full workouts vs partial workouts that are specific to one section, e.g. warmups or core workouts
    # type is set to "full" for full workouts, and "section" for section-specific workouts
    # default is "full"
    fields=["id", "name", "workout_sections", "created_ts", "created_by", "type"]
    key_field="id"
    partition_value="workout"

    def __init__(self, d={}):
        super().__init__(d)

class MemberWorkoutDefinitionEntity (EntityObject):
    table_name="MemberWorkoutDefinitionTable"
    fields=["id", 
            "member_id", 
            "name", 
            "description", 
            "workout_sections", 
            "created_ts", 
            "created_by", 
            "base_workout_def_id",      # references a base workout definition if applicable
            "tags",                     # list of tags associated with the workout
            "member_program_id",        # reference the member program this workout is part of, if any
            "order_index"               # index to determine the order of workouts within a program
            ]
    key_field="id"
    partition_field="member_id"

    def __init__(self, d={}):
        super().__init__(d)

class MemberWorkoutInstanceEntity (EntityObject):
    table_name="MemberWorkoutInstanceTable"
    fields=["id", 
            'name',
            "member_id", 
            "workout_sections", 
            "started_ts", 
            "finished_ts", 
            "scheduled_workout_event_id", 
            "adjustments_for_next_workout",
            "member_workout_def_id",         # reference to the member workout definition from which this instance was created
            "member_program_id",              # reference to the member program this workout instance is part of, if any
            "member_program_name"             # name of the member program this workout instance is part of, if any
            ]
    key_field="id"
    partition_field="member_id"

    def __init__(self, d={}):
        super().__init__(d)


def get_exercises_from_workout(workout):
    exercises = []
    # check if workout has either 'sections' or 'workout_sections' field
    # then iterate through the correct field
    if 'sections' in workout:
        SECTION_FIELD = 'sections'
    elif 'workout_sections' in workout:
        SECTION_FIELD = 'workout_sections'
    else:
        return exercises
    for s in workout[SECTION_FIELD]:
        for it in s['exercises']:
            ex = get_entity("ExerciseTable", it['id'])
            if ex:
                ex['parameters'] = it['parameters']
                exercises.append(ex)
    return exercises

        
