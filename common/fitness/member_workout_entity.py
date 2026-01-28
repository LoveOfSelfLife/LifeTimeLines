from common.entity_store import EntityObject


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

class MemberWorkouDefinitionEntity (EntityObject):
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
            "member_program_id"         # reference the member program this workout is part of, if any
            ]
    key_field="id"
    partition_field="member_id"

    def __init__(self, d={}):
        super().__init__(d)

class MemberWorkoutInstanceEntity (EntityObject):
    table_name="MemberWorkoutInstanceTable"
    fields=["id", 
            "member_id", 
            "workout_sections", 
            "started_ts", 
            "finished_ts", 
            "scheduled_workout_event_id", 
            "adjustments_for_next_workout",
            "member_workout_def_id",         # reference to the member workout definition from which this instance was created
            "member_program_id"              # reference to the member program this workout instance is part of, if any
            ]
    key_field="id"
    partition_field="member_id"

    def __init__(self, d={}):
        super().__init__(d)

def initialize_mbr_wkt_instance(mbr_wkt_inst, 
                                member_id, 
                                workout_sections, 
                                started_ts, 
                                finished_ts, 
                                scheduled_workout_event_id, 
                                adjustments_for_next_workout,
                                member_workout_def_id,
                                member_program_id):
    mbr_wkt_inst['member_id'] = member_id
    mbr_wkt_inst['workout_sections'] = workout_sections
    mbr_wkt_inst['started_ts'] = started_ts
    mbr_wkt_inst['finished_ts'] = finished_ts
    mbr_wkt_inst['scheduled_workout_event_id'] = scheduled_workout_event_id
    mbr_wkt_inst['adjustments_for_next_workout'] = adjustments_for_next_workout
    mbr_wkt_inst['member_workout_def_id'] = member_workout_def_id
    mbr_wkt_inst['member_program_id'] = member_program_id
    return mbr_wkt_inst

        
