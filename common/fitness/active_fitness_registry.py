from common.fitness.program_entity import ProgramEntity
from common.fitness.member_entity import MemberEntity
from common.fitness.exercise_entity import ExerciseEntity, ExerciseReviewEntity, exercise_entity_filter, exercise_entity_filter_term, render_exercise_popup_viewer_html
from common.fitness.member_entity import MemberEntity
from common.fitness.workout_entity import WorkoutEntity

editable_entities = {
    "MemberTable" : { "entity_class": MemberEntity, 
                      "listing_view_fields": ["name", "short_name", "email"]
                    },
    "ExerciseTable" : { "entity_class": ExerciseEntity,
                        "listing_view_fields": ["name", "category"],
                        "filters": [
                            {
                                "type" : "choice",
                                "id" : "reviewed",
                                "label" : "Reiewed?",
                                "options" : [
                                    { "label" : "All", "value" : "" },
                                    { "label" : "Not Reviewed", "value" : "no" },
                                    { "label" : "Reviewed", "value" : "yes" }
                                ]
                            },
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
