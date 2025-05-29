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
            "setCompletionMeasure", "udf1", "udf2"]
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
    """Filter out exercises that are marked as "hide" in the ExerciseReviewTable
    """
    review = get_entity("ExerciseReviewTable", exercise.get("id", ""))
    if review is not None:
        if "disposition" in review and "hide" in review["disposition"]:
            return True  # This exercise is hidden

    return False  # For now, we assume all exercises are visible.


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
        if term.get("id") == "category":
            if term_value and term_value != "":
                # check the category field of the entity
                entity_category = entity.get("category", None)
                if entity_category is None:
                    return False
                if term_value not in entity_category.lower():
                    return False
                continue
        if term.get("id") == "reviewed":
            if term_value and term_value != "":
                # check the reviewed field of the entity
                # if the entity has a review, then it is considered reviewed
                # if the entity does not have a review, then it is not considered reviewed
                # if the term_value is "yes", then we check if the entity has a review
                # if the term_value is "no", then we check if the entity does not have a review
                if term_value not in ["yes", "no"]:
                    return False
                if term_value == "yes":
                    # if the term_value is "yes", then we check if the entity has a review
                    if not exercise_was_reviewed(entity):
                        return False
                elif term_value == "no":
                    # if the term_value is "no", then we check if the entity does not have a review
                    if exercise_was_reviewed(entity):
                        return False
                continue
        if term.get("id") == "level":
            if term_value and term_value != "":
                entity_level = entity.get("level", None)
                if entity_level is None:
                    return False
                if term_value not in entity_level.lower():
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


def exercise_entity_filter_term(args={}):
    return [
        {
            "label": "Filter Text",
            "id": "text",
            "value": args.get('text', ''),
        },
        {
            "label": "Category",
            "id": "category",
            "value": args.get('category', ''),
        },
        {
            "label": "Level",
            "id": "level",
            "value": args.get('level', ''),
        },
        {
            "label": "Reviewed?",
            "id": "reviewed",
            "value": args.get('reviewed', ''),
        }
    ]


def render_exercise_popup_viewer_html(context, entity):
    return hx_render_template('_exercise_details_form.html',
                              exercise=entity,
                            #   schema=schema,
                            #   table_id=table_id, 
                              errors={},
                              context=context)