from common.fitness.active_fitness import ProgramEntity
from common.fitness.member_info import MemberEntity
from common.fitness.exercise_entity import ExerciseEntity
from common.fitness.member_info import MemberEntity

class ActiveFitnessRegistry:
    editable_entities = {
        "members" : { "entity": MemberEntity(), 
                      "listing_view_fields": ["id", "name", "short_name", "email", "level", "is_active", "is_admin"],
                     },
        "exercises" : { "entity": ExerciseEntity(),
                        "listing_view_fields": ["name", "category"],
                       },
        "programs" : { "entity": ProgramEntity(),
                        "listing_view_fields": ["id", "name"]
                       }
                      }
    non_editable_entities = {
    }
    entities = {**editable_entities, **non_editable_entities}

def get_fitnessclub_entity_names():
    return list(ActiveFitnessRegistry.editable_entities.keys())

def get_fitnessclub_entity_by_name(name):
    entry = ActiveFitnessRegistry.editable_entities.get(name, None)
    if entry:
        return entry["entity"], entry["listing_view_fields"]
    return None, None
