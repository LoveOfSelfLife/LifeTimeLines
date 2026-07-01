from common.fitness.active_fitness_registry import get_fitnessclub_listing_fields_for_entity
from common.fitness.entities_getter import get_entities, get_filtered_entities


def find_exercises_satisfying_constraints(constraints, member_id=None):
    # constraints is a dictionary where keys are attribute names and values are the desired values
    filter_terms = []
    for attribute, value in constraints.items():
        filter_terms.append({"type": "attribute", "attribute": attribute, "value": value})
    exercises = get_filtered_entities("ExerciseTable", filter_terms, member_id=member_id)
    return exercises

def find_exercises_by_movement_category(movement_category, member_id=None):
    return find_exercises_satisfying_constraints({"movement_category": movement_category}, member_id=member_id)
