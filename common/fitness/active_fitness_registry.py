from common.fitness.program_entity import ProgramEntity
from common.fitness.member_entity import MemberEntity
from common.fitness.exercise_entity import ExerciseEntity, ExerciseReviewEntity, exercise_entity_filter, exercise_entity_filter_term, render_exercise_popup_viewer_html
from common.fitness.exercise_entity import exercise_filters
from common.fitness.member_entity import MemberEntity
from common.fitness.workout_entity import WorkoutEntity

editable_entities = {
    "MemberTable" : { "entity_class": MemberEntity, 
                      "listing_view_fields": ["name", "short_name", "email"],
                        "card_view_fields": { "title" : lambda e: e['name'] if 'name' in e else "",
                                              "subtitle" : lambda e: e['short_name'] if 'short_name' in e else "",
                                              "image_url" : lambda e: e['image_url'] if 'image_url' in e else "",
                                              "description" : lambda e: e['email'] if 'email' in e else ""
                                             }
                    },
    "ExerciseTable" : { "entity_class": ExerciseEntity,
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
    "ProgramTable" : { "entity_class": ProgramEntity,
                        "listing_view_fields": ["name"],
                        "card_view_fields": { "title" : lambda e: e['name'] if 'name' in e else "",
                                              "subtitle" : lambda e: "Start Date: " + e['start_date'] if 'start_date' in e else "",
                                              "image_url" : None,
                                              "description" : lambda e: ""
                                             }                        
                    },
    "WorkoutTable" : { "entity_class": WorkoutEntity,
                        "listing_view_fields": ["name"],
                        "card_view_fields": { "title" : lambda e: e['name'] if 'name' in e else "",
                                              "subtitle" : lambda e: "",
                                              "image_url" : None,
                                              "description" : lambda e: ""
                                             }
                    },
    "ExerciseReviewTable" : 
                    { "entity_class": ExerciseReviewEntity,
                      "listing_view_fields": ["name"],
                        "card_view_fields": { "title" : lambda e: e['name'] if 'name' in e else "",
                                              "subtitle" : lambda e: "",
                                              "image_url" : None,
                                              "description" : lambda e: ""
                                             }
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
