from common.fitness.exercise_entity import ExerciseEntity, exercise_facets


def get_fitnessclub_facets_for_entity(entity_name):
    if entity_name == ExerciseEntity.table_name:
        return exercise_facets
    return None
