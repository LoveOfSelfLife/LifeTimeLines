from hashlib import sha256
from common.entity_store import EntityObject
from common.fitness.entities_getter import get_entity
from common.fitness.hx_common import hx_render_template
from common.fitness.utils import convert_to_alphanumeric
import json
from common.fitness.exercise_schema import exercise_schema
from common.fitness.exercise_schema import exercise_review_schema

class ExerciseEntity (EntityObject):
    table_name="ExerciseTable"
    fields=["id", "type", "name", "force", "level", "mechanic", "equipment", "equipment_detail", 
            "origin",  "primaryMuscles", "secondaryMuscles", "instructions", "category", "images", "videos", 
            "setCompletionMeasure", "udf1", "udf2", "physical_fitness_components", "hide"]
    key_field="id"
    partition_value="exercise"
    schema = exercise_schema

    def __init__(self, d={}):
        super().__init__(d)

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


def is_exercise_hidden(exercise):
    """Filter out exercises that are marked as "hide" 
    """
    hide = exercise.get("hide", None)
    return hide

def matches_filter(entity,term):
    if term is None:
        return True
    term = term.lower()
    terms = term.split()
    for t in terms:
        for field in entity.get_fields():
            if field in entity and isinstance(entity[field], str):
                if term in entity[field].lower():
                    return True
    return False

def exercise_was_reviewed(exercise):
    """Check if an exercise was reviewed by looking it up in the ExerciseReviewTable."""
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



def exercise_entity_filter_term(args={}):
    terms = [ {"id": f['id'], 
               "label": f['label'], 
               "shortlabel": f['shortlabel'],  
               "value": args.get(f['id'], '')} for f in exercise_filters ]
    return terms
    
    # return [
    #     {
    #         "label": "Filter Text",
    #         "id": "text",
    #         "value": args.get('text', ''),
    #     },
    #     {
    #         "label": "Physical Fitness Component",
    #         "id": "physical_fitness_components",
    #         "value": args.get('physical_fitness_components', '')
    #     },
    #     {
    #         "label": "Muscle",
    #         "id": "muscle",
    #         "value": args.get('muscle', '')
    #     }
    # ]




def matches_all_terms_in_filter(entity, filter_term):
    for term in filter_term:
        term_value = term.get("value", None)
        term_value = term_value.lower() if term_value is not None else None
        if term.get("id", None) == "text":
            if term_value and term_value != "":
                # if there is a non-empty value for the text filter term
                # then we check the entire entity to see if the term is in any of the fields
                # if it does match, then we continue to check the other filter terms
                # if it does not match, no need to check the other filter terms
                # and we return False
                if matches_filter(entity, term_value):
                    continue
                else:
                    return False
        if term.get("id") == "physical_fitness_components":
            if term_value and term_value != "":
                # check the PF component field of the entity
                entity_component = entity.get("physical_fitness_components", [])
                if len(entity_component) == 0:
                    return False
                if term_value not in entity_component:
                    return False
                continue
        if term.get("id") == "muscle":
            if term_value and term_value != "":
                entity_prime_muscles = entity.get("primaryMuscles", [])
                entity_secondary_muscles = entity.get("secondaryMuscles", [])
                muscles = entity_prime_muscles + entity_secondary_muscles
                if len(muscles) == 0:
                    return False
                if term_value not in [m.lower() for m in muscles]:
                    return False
                continue
    return True


def exercise_entity_filter(entities, filter_term):
    # filter_term is a list of dictionaries
    # each dictionary has an id and a value
    # for example: [{"id": "text", "value": "squat"}, {"id": "category", "value": "core"}]
    # in order for an entity from the list of entities to be included in the result
    # it must match all the filter terms where the value for that filter term is not empty
    # if the value for a filter term is empty, it is ignored
    # first remove all exercises that are hidden
    entities = [e for e in entities if not is_exercise_hidden(e)]

    if filter_term is None:
        return entities
    if len(filter_term) == 0:
        return entities
    filtered_entities = []
    for entity in entities:
        if matches_all_terms_in_filter(entity, filter_term):
            filtered_entities.append(entity)
    return filtered_entities


def render_exercise_popup_viewer_html(context, entity):
    return hx_render_template('_exercise_details_form.html',
                              exercise=entity,
                              errors={},
                              context=context)
