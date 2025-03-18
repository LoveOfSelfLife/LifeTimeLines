
# from services.fitnessclub.active_fitness import ProgramEntity, MemberEntity, ExerciseEntity
from active_fitness import ProgramEntity, MemberEntity
from services.fitnessclub.exercises import ExerciseEntity

class ActiveFitnessRegistry:
    editable_entities = {
        "members" : MemberEntity(),
        "programs" : ProgramEntity()
    }
    non_editable_entities = {
    }
    entities = {**editable_entities, **non_editable_entities}

def get_active_fitness_entity_names():
    return list(ActiveFitnessRegistry.editable_entities.keys())

def get_active_fitness_entity_by_name(name):
    return ActiveFitnessRegistry.editable_entities.get(name, None)
