from hashlib import sha256
from common.entity_store import EntityObject
from common.fitness.hx_common import hx_render_template
from common.fitness.utils import convert_to_alphanumeric
import json
from common.fitness.exercise_schema import exercise_schema
from common.fitness.exercise_schema import exercise_review_schema

class ExerciseEntity (EntityObject):
    table_name="ExerciseTable"
    fields=["id", "type", "name", "force", "level", "mechanic", "equipment", "equipment_detail", "equipment_list",
            "origin",  "primaryMuscles", "secondaryMuscles", "instructions", "category", "images", "videos", "gif",
            "created_by_member_id", 
            "setCompletionMeasure", 
            "resistance_doubled", # has a boolean value
            "only_one_set", # has a boolean value
            "udf1", "udf2", 
            "physical_fitness_components", 
            "movement_categories", 
            "hide"]
    
    key_field="id"
    partition_value="exercise"
    schema = exercise_schema

    def __init__(self, d={}):
        super().__init__(d)

    def is_resistance_doubled(self):
        if self.get("resistance_doubled", None) is not None:
            return self.get("resistance_doubled")
        # default resistance doubled is False, which means that the weight lifted is the same as the actual resistance specified for the exercise,
        # if resistance doubled is True, it means that the weight indicated is for each hand, so the total weight lifted is double the resistance specified for the exercise
        return False

    def is_only_one_set(self):
        # some exercises i.e. activities are only meant to be done once, e.g. a 5k run, a session of playing pickleball, etc. for these exercises, we set the onlyOneSet field to true, 
        # therefore in the workout view we can use this information to simplify the Ux to avoid having to ask for # sets
        if self.get("only_one_set", None) is not None:
            return self.get("only_one_set")
        return False

    def get_set_completion_measure(self):
        # the setCompletionMeasure field indicates what measure is used to determine if a set of the exercise is completed, e.g. "reps", "time", "distance", "other"
        # if the field is not specified for an exercise, we default to "reps"
        return self.get("setCompletionMeasure", "reps")
    
    def exercises_uses_external_force(self):
        # this function is used to determine if the exercise uses an external force, which is the case if the exercise has a non-bodyweight equipment
        equipment = self.get("equipment", None)
        if not equipment or equipment.lower().startswith("body"):
            return False
        return True
    
class ExerciseReviewEntity (EntityObject):
    table_name="ExerciseReviewTable"
    fields=["id", "name", "category", "disposition", "setCompletionMeasure", "comments"]
    key_field="id"
    partition_value="review"
    schema = exercise_review_schema

    def __init__(self, d={}):
        super().__init__(d)

class ExerciseIndexEntity (EntityObject):
    table_name="ExerciseIndexTable"
    fields=["exercise_value", "exercise_attribute", "exercises_list" ]
    key_field="exercise_value"
    partition_field="exercise_attribute"

    def __init__(self, d={}):
        super().__init__(d)

movement_category_to_section_map = {
    "CORE": "core",
    "CORE-AE": "core",
    "CORE-AF": "core",
    "CORE-AR": "core",
    "CORE-HF": "core",
    "CORE-ROT": "core",
    "HINGE-BRIDGE": "strength",
    "HINGE-SL": "strength",
    "HINGE-SYM": "strength",
    "PULL": "strength",
    "PULL-HORZ": "strength",
    "PULL-VERT": "strength",
    "PUSH": "strength",
    "PUSH-HORZ": "strength",
    "PUSH-VERT": "strength",
    "RAMP": "warmup",
    "SQUAT": "strength",
    "SQUAT-ASYM": "strength",
    "SQUAT-SL": "strength",
    "SQUAT-SYM": "strength",
}

def get_section_type_from_movement_category(movement_category):
    return movement_category_to_section_map.get(movement_category, None)

# the possible values for the physical_fitness_components property of an exercise are:
physical_fitness_components_to_section_map = {
    'balance': ['balance'],
    'aerobic': ['cardio'],
    'mobility': ['warmup'],
    'power': ['strength', 'power'],
    'strength': ['strength'],
    'Core': ['core'],
    'core': ['core'],
    'cardio': ['cardio', 'warmup'],
    'endurance': ['cardio'],
    'myofascia': ['warmup'],
    'flexibility': ['warmup'],
}
def get_section_types_from_physical_fitness_components(physical_fitness_components):
    section_types = set()
    for pfc in physical_fitness_components:
        section_types.update(physical_fitness_components_to_section_map.get(pfc, []))
    return list(section_types)


# the following are the possible values for the category property of an exercise, and the corresponding section_type they belong to:
category_to_section_map = {
    "cardio": ["cardio", "warmup"],
    "core": ["core"],
    "mobility": ["warmup"],
    "olympic weightlifting": ["strength"],
    "plyometrics": ["strength"],
    "powerlifting": ["strength", "power"],
    "strength": ["strength"],
    "stretching": ["warmup"],
    "strongman": ["strength", "power"],
    "warmup": ["warmup"],
}
def get_section_types_from_category(category):
    return category_to_section_map.get(category, [])

def does_exercise_belong_in_section(exercise, section_type):
    """Check if an exercise belongs in a given section.

    Args:
        exercise (dict): The exercise entity.
        section_type (str): The section type to check against.

    Returns:
        bool: True if the exercise belongs in the section, False otherwise.

    These are the section types currently supported:
        warmup
        core
        power
        combination
        strength
        balance
        cardio
    """
    if not exercise or not section_type:
        return False
    # lets check if the exercise has a section attribute, if yes, then we can use that to determine if it belongs in the section
    if "section" in exercise and exercise["section"] is not None:
        if isinstance(exercise["section"], list):
            # If the section attribute is a list, check if the section_type is in the list
            if section_type in [s for s in exercise["section"]]:
                return True
        else:
            # If the section attribute is a string, check for a direct match
            if section_type == str(exercise["section"]):
                return True

    # next we check movement_categories
    # if the exercise has a movement_category attribute, we can check section_type against the movement_category
    # we use the movement_category_to_section_map to map the movement_category to a section_type
    if 'movement_categories' in exercise and exercise['movement_categories'] is not None:
        if isinstance(exercise['movement_categories'], list):
            # If the movement_categories attribute is a list, check if the section_type is in the list
            # Map each movement category to its section and check against section_type
            mapped_sections = [get_section_type_from_movement_category(s) for s in exercise['movement_categories']]
            if section_type in mapped_sections:
                return True
        else:
            # If the movement_categories attribute is a string, map it to its section and check for a match
            mapped_section = get_section_type_from_movement_category(str(exercise['movement_categories']))
            if section_type == mapped_section:
                return True
            
    # next we will check the category property
    # if the exercise has a category attribute, we can map the category to a section_type using the category_to_section_map
    # then check if the section_type is in the mapped section_types
    # the category value will be a string

    if 'category' in exercise and exercise['category'] is not None:
        mapped_sections = get_section_types_from_category(str(exercise['category']))
        if section_type in mapped_sections:
            return True

    # next we will check the physical_fitness_components property
    # if the exercise has a physical_fitness_components attribute, we can map the physical_fitness_components to section_types using the physical_fitness_components_to_section_map
    # then check if the section_type is in the mapped section_types

    if 'physical_fitness_components' in exercise and len(exercise['physical_fitness_components']) > 0:
        mapped_sections = []
        for pfc in exercise['physical_fitness_components']:
            mapped_sections.extend(get_section_types_from_physical_fitness_components([pfc]))
        if section_type in mapped_sections:
            return True
    return False

def are_these_exercises_related(exercise_entity, general_exercise_entity):
    """Check if an exercise entity is related to a general exercise entity based on shared attributes."""
    if not exercise_entity or not general_exercise_entity:
        return False

    # here we want to check if the exercise_entity and general_exercise_entity share any of the following attributes:
    # 1. movement_categories, 2. physical_fitness_components, 3. primaryMuscles

    # Check for shared movement categories
    movement_categories = set(exercise_entity.get("movement_categories", []))
    general_movement_categories = set(general_exercise_entity.get("movement_categories", []))
    shared_movement_categories = movement_categories.intersection(general_movement_categories)

    if shared_movement_categories:
        return True

    # if the exercise does not have movement_categories, we will use a combination of physical_fitness_components and primary muscles 
    # to determine relatedness

    """
    these are the possible pfc values:  
    'balance'
    'aerobic'
    'mobility'
    'power'
    'strength'
    'Core'
    'core'
    'cardio'
    'endurance'
    'myofascia'
    'flexibility

    first we check which PFC values are shared
    if any of these are shared: balance, aerobic, mobiility, power, core or Core, cardio, endurance, myofascia or flexibility then we consider the exercises related
    however, if the only shared PFC values are strength, then we will check if they share any primary muscles, if yes, then we consider them related, otherwise not related
    """

    pfc_values = exercise_entity.get("physical_fitness_components", [])
    general_pfc_values = general_exercise_entity.get("physical_fitness_components", [])

    shared_pfc  = set(pfc_values).intersection(set(general_pfc_values))
    if shared_pfc:
        if 'strength' in shared_pfc and len(shared_pfc) == 1:
            # if the only shared section type is strength, then we will check if they share any primary muscles
            primary_muscles = set(exercise_entity.get("primaryMuscles", []))
            general_primary_muscles = set(general_exercise_entity.get("primaryMuscles", []))
            shared_primary_muscles = primary_muscles.intersection(general_primary_muscles)
            if shared_primary_muscles:
                return True
            else:
                return False
        else:
            return True
    
    return False

def gen_exercise_id(exercise):
    """Generate an exercise id from the exercise name."""
    # run a hash on the exercise json and use that has as part of the id
    hash = sha256()
    hash.update(bytes(json.dumps(exercise), 'utf-8'))
    h = hash.hexdigest()
    alphanum = convert_to_alphanumeric(exercise["name"])
    id = f'{alphanum}-{h[0:16]}'

    return id

    # id = f'{exercise["name"].replace(" ", "-").lower()}-{h}'

    return id


def exercise_was_reviewed(exercise):
    """Check if an exercise was reviewed by looking it up in the ExerciseReviewTable."""
    from common.fitness.entities_getter import get_entity
    review = get_entity("ExerciseReviewTable", exercise.get("id", ""))
    if review is not None:
        # check if the review has a disposition
        if "disposition" in review and review["disposition"] is not None:
            return True
        # check if there are any comments, if yes, then it is considered reviewed
        if "comments" in review and review["comments"] is not None:
            return True
        # check if there is a category, if yes, then it is considered reviewed
        if "category" in review and review["category"] is not None:
            return True
    return False  # otherwise, the exercise does not have a review

exercise_filters = [
                    {
                        "type" : "choice",
                        "id" : "physical_fitness_components",
                        "label" : "Physical Fitness Component",
                        "shortlabel" : "Component",
                        "options" : [
                            { "label" : "Any", "value" : "" },
                            { "label" : "Flexibility", "value" : "flexibility" },
                            { "label" : "Mobility", "value" : "mobility" },
                            { "label" : "Balance", "value" : "balance" },
                            { "label" : "Core", "value" : "core" },
                            { "label" : "Power", "value" : "power" },
                            { "label" : "Strength", "value" : "strength" },
                            { "label" : "Cardio", "value" : "cardio" },
                            { "label" : "Endurance", "value" : "endurance" },
                            { "label" : "Myofascia", "value" : "myofascia" }
                        ]
                    },
                    {
                        "type" : "choice",
                        "id" : "muscle",
                        "label" : "Muscle involved",
                        "shortlabel" : "Muscle",
                        "options" : [
                            { "label" : "Any", "value" : "" },
                            { "label" : "Abdominals", "value" : "abdominals" },
                            { "label" : "Adductors", "value" : "adductors" },
                            { "label" : "Abductors", "value" : "abductors" },                                    
                            { "label" : "Biceps", "value" : "biceps" },
                            { "label" : "Calves", "value" : "calves" },
                            { "label" : "Chest", "value" : "chest" },
                            { "label" : "Forearms", "value" : "forearms" },
                            { "label" : "Glutes", "value" : "glutes" },
                            { "label" : "Hamstrings", "value" : "hamstrings" },
                            { "label" : "Lats", "value" : "lats" },
                            { "label" : "Lower Back", "value" : "lower_back" },
                            { "label" : "Middle Back", "value" : "middle_back" },
                            { "label" : "Neck", "value" : "neck" },
                            { "label" : "Quadriceps", "value" : "quadriceps" },
                            { "label" : "Shoulders", "value" : "shoulders" },
                            { "label" : "Traps", "value" : "traps" },
                            { "label":  'Triceps', 'value': 'triceps' }
                        ]
                    },
                    {
                        "type" : "text",
                        "id" : "text",
                        "label" : "Filter Text",
                        "shortlabel" : "Text"
                    }
                ]


def render_exercise_popup_viewer_html(context, entity, can_edit=False, filter_terms=[]):
    return hx_render_template('_exercise_details_form.html',
                              exercise=entity,
                              errors={},
                              context=context,
                              can_edit=can_edit)
