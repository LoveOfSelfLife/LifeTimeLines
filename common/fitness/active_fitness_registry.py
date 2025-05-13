from common.fitness.program_entity import ProgramEntity
from common.fitness.member_entity import MemberEntity
from common.fitness.exercise_entity import ExerciseEntity
from common.fitness.member_entity import MemberEntity
from common.fitness.workout_entity import WorkoutEntity

editable_entities = {
    "MemberTable" : { "entity_class": MemberEntity, 
                      "listing_view_fields": ["name", "short_name", "email"]
                    },
    "ExerciseTable" : { "entity_class": ExerciseEntity,
                        "listing_view_fields": ["name", "category"]
                    },
    "ProgramTable" : { "entity_class": ProgramEntity,
                        "listing_view_fields": ["name"]
                    },
    "WorkoutTable" : { "entity_class": WorkoutEntity,
                        "listing_view_fields": ["name"]
                    }
    }

def get_fitnessclub_entity_names():
    return list(editable_entities.keys())


def get_fitnessclub_entity_type_for_entity(entity_name):
    entry = editable_entities.get(entity_name, None)
    if entry:
        return entry["entity_class"]()
    return None, None

def get_fitnessclub_listing_fields_for_entity(entity_name):
    entry = editable_entities.get(entity_name, None)
    if entry:
        return entry["listing_view_fields"]
    return None, None
