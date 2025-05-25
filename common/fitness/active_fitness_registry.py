from common.fitness.program_entity import ProgramEntity
from common.fitness.member_entity import MemberEntity
from common.fitness.exercise_entity import ExerciseEntity, ExerciseReviewEntity
from common.fitness.member_entity import MemberEntity
from common.fitness.workout_entity import WorkoutEntity
from common.fitness.hx_common import hx_render_template


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
        }
    ]
def exercise_entity_filter(entities, filter_term):
    # filter_term is a list of dictionaries
    # each dictionary has an id and a value
    # for example: [{"id": "text", "value": "squat"}, {"id": "category", "value": "core"}]
    # in order for an entity from the list of entities to be included in the result
    # it must match all the filter terms where the value for that filter term is not empty
    # if the value for a filter term is empty, it is ignored
    if filter_term is None:
        return entities
    if len(filter_term) == 0:
        return entities
    filtered_entities = []
    for entity in entities:
        if matches_all_terms_in_filter(entity, filter_term):
            filtered_entities.append(entity)
    return filtered_entities

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
        if term.get("id") == "level":
            if term_value and term_value != "":
                entity_level = entity.get("level", None)
                if entity_level is None:
                    return False
                if term_value not in entity_level.lower():
                    return False
                continue

    return True

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

def render_exercise_popup_viewer_html(context, entity):
    return hx_render_template('_exercise_details_form.html', 
                              exercise=entity,
                            #   schema=schema,
                            #   table_id=table_id, 
                              errors={},
                              context=context)    
    

# {'stretching', 'strength', '', 'strongman', 'plyometrics', 'powerlifting', 'cardio'}

                                    # { "label" : "warmup", "value" : "warmup" },
                                    # { "label" : "core", "value" : "core" },
                                    # { "label" : "power", "value" : "power" },
                                    
editable_entities = {
    "MemberTable" : { "entity_class": MemberEntity, 
                      "listing_view_fields": ["name", "short_name", "email"]
                    },
    "ExerciseTable" : { "entity_class": ExerciseEntity,
                        "listing_view_fields": ["name", "category"],
                        "filters": [
                            {
                                "type" : "choice",
                                "id" : "level",
                                "label" : "Level",
                                "options" : [
                                    { "label" : "All Levels", "value" : "" },
                                    { "label" : "Basic", "value" : "beginner" },
                                    { "label" : "Intermediate", "value" : "intermediate" },
                                    { "label" : "Advanced", "value" : "expert" }
                                ]
                            },
                            {
                                "type" : "choice",
                                "id" : "category",
                                "label" : "Category",
                                "options" : [
                                    { "label" : "All categories", "value" : "" },                                    
                                    { "label" : "strength", "value" : "strength" },
                                    { "label" : "cardio", "value" : "cardio" },
                                    { "label" : "stretching", "value" : "stretching" },
                                    { "label" : "plyometrics", "value" : "plyometrics" },
                                    { "label" : "strongman", "value" : "strongman" },
                                    { "label" : "powerlifting", "value" : "powerlifting" },
                                    { "label" : "olympic weightlifting", "value" : "olympic weightlifting" }
                                ]
                            },
                            {
                                "type" : "text",
                                "id" : "text",
                                "label" : "Filter Text"
                            }
                        ],
                        "filter_func" : exercise_entity_filter,
                        "filter_term_func" : exercise_entity_filter_term,
                        "entity_popup_viewer" : render_exercise_popup_viewer_html
                    },
    "ProgramTable" : { "entity_class": ProgramEntity,
                        "listing_view_fields": ["name"]
                    },
    "WorkoutTable" : { "entity_class": WorkoutEntity,
                        "listing_view_fields": ["name"]
                    },
    "ExerciseReviewTable" : 
                    { "entity_class": ExerciseReviewEntity,
                      "listing_view_fields": ["name"]
                    }
    }

def get_fitnessclub_entity_names():
    return list(editable_entities.keys())


def get_fitnessclub_entity_type_for_entity(entity_name):
    entry = editable_entities.get(entity_name, None)
    if entry:
        return entry["entity_class"]()
    return None, None

def get_fitnessclub_listing_fields_for_entity(entity_name):
    entry = editable_entities.get(entity_name, None)
    if entry:
        return entry["listing_view_fields"]
    return None

def get_fitnessclub_entity_filters_for_entity(entity_name):
    entry = editable_entities.get(entity_name, None)
    if entry:
        return entry.get("filters", None)
    return None

def get_fitnessclub_filter_func_for_entity(entity_name):
    entry = editable_entities.get(entity_name, None)
    if entry:
        return entry.get("filter_func", None)
    return None

def get_fitnessclub_filter_term_for_entity(entity_name):
    entry = editable_entities.get(entity_name, None)
    if entry:
        return entry.get("filter_term_func", None)
    return None

