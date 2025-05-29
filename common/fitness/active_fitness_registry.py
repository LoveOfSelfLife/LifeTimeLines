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
                            # {
                            #     "type" : "choice",
                            #     "id" : "reviewed",
                            #     "label" : "Reiewed?",
                            #     "options" : [
                            #         { "label" : "All", "value" : "" },
                            #         { "label" : "Not Reviewed", "value" : "no" },
                            #         { "label" : "Reviewed", "value" : "yes" }
                            #     ]
                            # },
                            {
                                "type" : "choice",
                                "id" : "physical_fitness_components",
                                "label" : "Physical Fitness Component",
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
