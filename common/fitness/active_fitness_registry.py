from ast import literal_eval
from flask import url_for
from common.entity_store import EntityObject, EntityStore

from common.fitness.entity_constants import PROGRAM_ENTITY_NAME, WORKOUT_ENTITY_NAME, WORKOUT_INSTANCE_ENTITY_NAME
from common.fitness.member_entity import MemberEntity, get_member_name_from_member_id
from common.fitness.exercise_entity import ExerciseEntity, ExerciseReviewEntity
from common.fitness.exercise_entity import exercise_filters
from common.fitness.member_entity import MemberEntity
from common.fitness.member_program_entity import MemberProgramsEntity

def extract_image_url(entity):
    # lambda e: e['images'][0]['url'] if 'images' in e and len(e['images']) > 0 else None
    if 'gif' in entity and entity['gif']:
        return entity['gif']
    if 'images' in entity and isinstance(entity['images'], list) and len(entity['images']) > 0:
        return entity['images'][0].get('url', None)
    return None

editable_entities = {
    "MemberTable" : { 
                      "listing_view_fields": [ "name",
                                               "short_name",
                                               "email",
                                               "role"
                                            ],
                        "card_view_fields": [ "title",
                                             "subtitle",
                                             "image_url",
                                             "description"
                                           ],
                        "field_mapping" :  { "name" : lambda e: e['name'] if 'name' in e else "",
                                             "title" : lambda e: e['name'] if 'name' in e else "",
                                              "subtitle" : lambda e: e['short_name'] if 'short_name' in e else "",
                                              "short_name" : lambda e: e['short_name'] if 'short_name' in e else "",
                                              "role" : lambda e: e['role'] if 'role' in e else "",
                                              "image_url" : lambda e: e['image_url'] if 'image_url' in e else "",
                                              "description" : lambda e: f"{e['email']} ({e.get('role', 'client')})" if 'email' in e else ""
                                             },
                    },
    "TeamTable" : {
                        "listing_view_fields": ["name", 
                                                "location", 
                                                "status"
                                                ],
                        "card_view_fields": [ "title",
                                             "subtitle",
                                             "image_url",
                                             "description"
                                           ],
                        "field_mapping": { 
                                            "name" : lambda e: e['name'] if 'name' in e else "",                                            
                                            "title" : lambda e: e['name'] if 'name' in e else "",
                                            "subtitle" : lambda e: e['location'] if 'location' in e else "",
                                            "image_url" : None,
                                            "description" : lambda e: e['description'] if 'description' in e else ""
                                             }

                    },
    "ExerciseTable" : { 
                        "listing_view_fields": ["name", 
                                                "category"
                                                ],
                        "card_view_fields": [ "title",
                                             "subtitle",
                                             "image_url",
                                             "description"
                                           ],
                        "field_mapping": { 
                                            "name" : lambda e: e['name'] if 'name' in e else "",                                            
                                            "title" : lambda e: e['name'] if 'name' in e else "",
                                            "subtitle" : lambda e: "",
                                            "image_url" : lambda e: extract_image_url(e),
                                            "description" : lambda e: ""
                                             },
                        "filters": exercise_filters
                    },
    PROGRAM_ENTITY_NAME : { 
                        "listing_view_fields": ["name", 
                                                "start", 
                                                "end", 
                                                "client"
                                                ],
                        "card_view_fields": [ "title",
                                              "subtitle",
                                              "image_url",
                                              "member"
                                            ],
                        "field_mapping": { "title" : lambda e: e['name'] if 'name' in e else "",
                                          "start" : lambda e: e['start_date'] if 'start_date' in e else "",
                                          "end" : lambda e: e['end_date'] if 'end_date' in e else "",
                                          "client" : lambda e: get_member_name_from_member_id(e.get('assigned_to_member_id')) if e.get('assigned_to_member_id') else "",
                                              "subtitle" : lambda e: (("" + (e['start_date'] if 'start_date' in e and e['start_date'] else "?")) + \
                                                                      (" to " + (e['end_date'] if 'end_date' in e and e['end_date'] else "?")) + \
                                                                        " - " + (get_member_name_from_member_id(e.get('assigned_to_member_id') or e.get('member_id')) if (e.get('assigned_to_member_id') or e.get('member_id')) else "")),
                                              "image_url" : None,
                                              "member" : lambda e: get_member_name_from_member_id(e.get('assigned_to_member_id') or e.get('member_id')) if (e.get('assigned_to_member_id') or e.get('member_id')) else "",
                                             }                        

                    },
    WORKOUT_ENTITY_NAME : { 
                        "listing_view_fields": ["name", "client", "program"],
                        "card_view_fields": [ "title",
                                              "subtitle",
                                              "image_url",
                                              "description"
                                            ],
                        "field_mapping": { "title" : lambda e: e['name'] if 'name' in e else "",
                                          "client" : lambda e: get_member_name_from_member_id(e.get('assigned_to_member_id')) if e.get('assigned_to_member_id') else "",
                                              "subtitle" : lambda e: "" + get_member_name_from_member_id(e.get('assigned_to_member_id') or e.get('member_id')) if (e.get('assigned_to_member_id') or e.get('member_id')) else "",
                                              "image_url" : lambda e: url_for('static', filename='images/workout_image.png'),
                                              "description" : lambda e: "",
                                              "program" : lambda e: get_program_name_from_program_id(e.get('member_program_id')) if e.get('member_program_id') else ""
                                             }

                    },
    WORKOUT_INSTANCE_ENTITY_NAME : { 
                        "listing_view_fields": ["name", "date", "program"],
                        "card_view_fields": [ "title",
                                              "subtitle",
                                              "image_url",
                                              "description"
                                            ],
                        "field_mapping": { "title" : lambda e: e['name'] if 'name' in e else "",
                                          "date" : lambda e: e['finished_ts'] if 'finished_ts' in e else "",
                                          "client" : lambda e: get_member_name_from_member_id(e.get('assigned_to_member_id')) if e.get('assigned_to_member_id') else "",
                                              "subtitle" : lambda e: "" + get_member_name_from_member_id(e.get('assigned_to_member_id') or e.get('member_id')) if (e.get('assigned_to_member_id') or e.get('member_id')) else "",
                                              "image_url" : lambda e: url_for('static', filename='images/workout_image.png'),
                                              "description" : lambda e: "",
                                              "program" : lambda e: get_program_name_from_program_id(e.get('member_program_id')) if e.get('member_program_id') else ""
                                             }

                    },
    "ExerciseReviewTable" : 
                    { 
                      "listing_view_fields": ["name"],
                        "card_view_fields": [ "title",
                                              "subtitle",
                                              "image_url",
                                              "description"
                                            ],
                        "field_mapping": { "title" : lambda e: e['name'] if 'name' in e else "",
                                              "subtitle" : lambda e: "",
                                              "image_url" : None,
                                              "description" : lambda e: ""
                                             }
                    },
    "ProgramWorkoutTable" : { 

                    }
    }

def get_program_name_from_program_id(program_id):
    if not program_id:
        return None
    from common.fitness.entities_getter import get_entity
    program_entity = get_entity(MemberProgramsEntity.table_name, program_id)
    if program_entity:
        return program_entity.get('name', None)
    return None
def get_fitnessclub_entity_names():
    return list(editable_entities.keys())

def get_entity_obj_from_entity_name(entity_name):
    return EntityObject.get_entity_class_from_table_name(entity_name)()

def get_fitnessclub_listing_fields_for_entity(entity_name):
    entry = editable_entities.get(entity_name, None)
    if entry:
        return {
                "listing_view": entry.get("listing_view_fields", None),
                "card_view": entry.get("card_view_fields", None),
                "field_mapping": entry.get("field_mapping", None)
                }
    return None

def get_fitnessclub_entity_filters_for_entity(entity_name):
    entry = editable_entities.get(entity_name, None)
    if entry:
        return entry.get("filters", None)
    return None


