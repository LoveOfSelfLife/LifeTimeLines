from common.fitness.active_fitness import ProgramEntity
from common.fitness.member_info import MemberEntity
from common.fitness.exercises import ExerciseEntity
from common.fitness.member_info import MemberEntity

class ActiveFitnessRegistry:
    editable_entities = {
        "members" : MemberEntity(),
        "exercises" : ExerciseEntity(),
        "programs" : ProgramEntity()
    }
    non_editable_entities = {
    }
    entities = {**editable_entities, **non_editable_entities}

def get_active_fitness_entity_names():
    return list(ActiveFitnessRegistry.editable_entities.keys())

def get_active_fitness_entity_by_name(name):
    return ActiveFitnessRegistry.editable_entities.get(name, None)
