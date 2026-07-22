from hashlib import sha256
from common.entity_store import EntityObject
from common.fitness.hx_common import hx_render_template
from common.fitness.utils import convert_to_alphanumeric
import json
from common.fitness.exercise_schema import exercise_schema
from common.fitness.exercise_schema import exercise_review_schema

class ExerciseEntity (EntityObject):
    table_name="ExerciseTable"
    fields=["id", "type", "name", "force", "level", "mechanic", "equipment", "equipment_detail", 
            "origin",  "primaryMuscles", "secondaryMuscles", "instructions", "category", "images", "videos", "gif", 
            "setCompletionMeasure", 
            "resistance_doubled", # has a boolean value
            "only_one_set", # has a boolean value
            "udf1", "udf2", "physical_fitness_components", "hide"]
    
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


def render_exercise_popup_viewer_html(context, entity):
    return hx_render_template('_exercise_details_form.html',
                              exercise=entity,
                              errors={},
                              context=context)
