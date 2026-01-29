from ast import literal_eval
from flask import request, url_for
from common.entity_store import EntityObject
from common.fitness.entity_constants import WORKOUT_ENTITY_NAME
from common.fitness.program_entity import ProgramEntity
from common.fitness.member_entity import MemberEntity
from common.fitness.exercise_entity import ExerciseEntity, ExerciseReviewEntity, exercise_entity_filter, exercise_entity_filter_term, render_exercise_popup_viewer_html
from common.fitness.exercise_entity import exercise_filters
from common.fitness.member_entity import MemberEntity

editable_entities = {
    "MemberTable" : { 
                      "listing_view_fields": ["name", "short_name", "email"],
                        "card_view_fields": { "title" : lambda e: e['name'] if 'name' in e else "",
                                              "subtitle" : lambda e: e['short_name'] if 'short_name' in e else "",
                                              "image_url" : lambda e: e['image_url'] if 'image_url' in e else "",
                                              "description" : lambda e: e['email'] if 'email' in e else ""
                                             }
                    },
    "ExerciseTable" : { 
                        "listing_view_fields": ["name", "category"],
                        "card_view_fields": { "title" : lambda e: e['name'],
                                              "subtitle" : lambda e: "Muscles: " + (", ".join(e['primaryMuscles']) if 'primaryMuscles' in e else ""),
                                              "image_url" : lambda e: e['images'][0]['url'] if 'images' in e and len(e['images']) > 0 else None,
                                              "description" : lambda e: "Components: " + (", ".join(e['physical_fitness_components']) if 'physical_fitness_components' in e else "")
                                             },
                        "filters": exercise_filters,
                        "filter_func" : exercise_entity_filter,
                        "filter_term_func" : exercise_entity_filter_term,
                        "entity_popup_viewer" : render_exercise_popup_viewer_html
                    },
    "ProgramTable" : { 
                        "listing_view_fields": ["name", "start_date", "end_date"],
                        "card_view_fields": { "title" : lambda e: e['name'] if 'name' in e else "",
                                              "subtitle" : lambda e: (("Start Date: " + (e['start_date'] if 'start_date' in e and e['start_date'] else "?")) + \
                                                                      (" End Date: " + (e['end_date'] if 'end_date' in e and e['end_date'] else "?"))),
                                              "image_url" : None,
                                              "description" : lambda e: ""
                                             }                        
                    },
    WORKOUT_ENTITY_NAME : { 
                        "listing_view_fields": ["name"],
                        "card_view_fields": { "title" : lambda e: e['name'] if 'name' in e else "",
                                              "subtitle" : lambda e: "",
                                              "image_url" : lambda e: url_for('static', filename='images/workout_image.png'),
                                              "description" : lambda e: ""
                                             }
                    },
    "ExerciseReviewTable" : 
                    { 
                      "listing_view_fields": ["name"],
                        "card_view_fields": { "title" : lambda e: e['name'] if 'name' in e else "",
                                              "subtitle" : lambda e: "",
                                              "image_url" : None,
                                              "description" : lambda e: ""
                                             }
                    },
    "ProgramWorkoutTable" : { 

                    }
    }

def get_fitnessclub_entity_names():
    return list(editable_entities.keys())

def get_entity_obj_from_entity_name(entity_name):
    return EntityObject.get_entity_class_from_table_name(entity_name)()

def get_fitnessclub_listing_fields_for_entity(entity_name):
    entry = editable_entities.get(entity_name, None)
    if entry:
        return {
                "listing_view": entry.get("listing_view_fields", None),
                "card_view": entry.get("card_view_fields", None)
                }
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

def get_fitnessclub_filter_term_func_for_entity(entity_name):
    entry = editable_entities.get(entity_name, None)
    if entry:
        return entry.get("filter_term_func", None)
    return None

def get_filter_func(entity_name, args):
    filters = get_fitnessclub_entity_filters_for_entity(entity_name)

    if filters:
        filter_func  = get_fitnessclub_filter_func_for_entity(entity_name)
        filter_term_func  = get_fitnessclub_filter_term_func_for_entity(entity_name)
        filter_terms = filter_term_func(args)
    else:
        filter_func = None
        filter_terms = None
    return filter_func, filter_terms

def _get_filter_terms_from_request():
    """Extract search term from either POST form data or GET query parameters."""
    # Get search term from appropriate source
    search_term = ""
    if request.method == 'POST':
        search_term = request.form.get("search", "").lower()
    else:
        # Try filter parameter first, then search parameter
        filter_param = request.args.get('filter', '')
        # if filter_param is present and is a string, need to convert it to a python object
        # using ast.literal_eval
        if filter_param and isinstance(filter_param, str):
            import ast
            filter_param = ast.literal_eval(filter_param)

        if len(filter_param) > 0:
            return filter_param

        search_term = request.args.get('search', '')
    
    # Construct filter_terms if we have a search term
    return [{
        "type": "text",
        "id": "text", 
        "label": "Filter Text",
        "shortlabel": "Text",
        "value": search_term
    }] if search_term else []

