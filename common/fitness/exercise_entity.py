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

def  does_entity_belong_in_section(entity, section_name):
    """Check if an entity belongs in a given section based on its attributes."""
    if not entity or not section_name:
        return False
    sections_to_check = ["category", "physical_fitness_components", "movement_categories", "section"]
    # Check for shared section attribute
    for section in sections_to_check:
        entity_section_value = entity.get(section, None)
        if entity_section_value:
            if isinstance(entity_section_value, list):
                # If the attribute is a list, check if the section_name is in the list
                if section_name.lower() in [s.lower() for s in entity_section_value]:
                    return True
            else:
                # If the attribute is a string, check for a direct match
                if section_name.lower() == str(entity_section_value).lower():
                    return True

    return False

def is_entity_related_to_general(exercise_entity, general_exercise_entity):
    """Check if an exercise entity is related to a general exercise entity based on shared attributes."""
    if not exercise_entity or not general_exercise_entity:
        return False

    # # Check for shared primary muscles
    # primary_muscles = set(exercise_entity.get("primaryMuscles", []))
    # general_primary_muscles = set(general_exercise_entity.get("primaryMuscles", []))
    # if primary_muscles.intersection(general_primary_muscles):
    #     return True

    # # Check for shared secondary muscles
    # secondary_muscles = set(exercise_entity.get("secondaryMuscles", []))
    # general_secondary_muscles = set(general_exercise_entity.get("secondaryMuscles", []))
    # if secondary_muscles.intersection(general_secondary_muscles):
    #     return True

    # # Check for shared equipment
    # equipment = set(exercise_entity.get("equipment_list", []))
    # general_equipment = set(general_exercise_entity.get("equipment_list", []))
    # if equipment.intersection(general_equipment):
    #     return True

    # # Check for shared physical fitness components
    # physical_fitness_components = set(exercise_entity.get("physical_fitness_components", []))
    # general_physical_fitness_components = set(general_exercise_entity.get("physical_fitness_components", []))
    # if physical_fitness_components.intersection(general_physical_fitness_components):
    #     return True

    # Check for shared movement categories
    movement_categories = set(exercise_entity.get("movement_categories", []))
    general_movement_categories = set(general_exercise_entity.get("movement_categories", []))
    if movement_categories.intersection(general_movement_categories):
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
