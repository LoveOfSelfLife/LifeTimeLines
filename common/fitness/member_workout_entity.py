
from flask import request

from common.entity_store import EntityObject
from common.entities_getter import get_entity
from common.fitness.fitness_presentation import assigned_client_name, member_name, program_name, workout_date, workout_image
from common.template_renderer import hx_render_template


class MemberWorkoutDefinitionEntity (EntityObject):
    table_name="MemberWorkoutDefinitionTable"
    fields=["id", 
            "name", 
            "description", 
            "workout_sections", 
            "created_ts", 
            "created_by", 
            "assigned_to_member_id",    # references the member to whom this workout is assigned
            "tags",                     # list of tags associated with the workout
            "member_program_id",        # reference the member program this workout is part of, if any
            "order_index",              # index to determine the order of workouts within a program
            "purpose",                  # optional field to describe the purpose of this workout within the context of a program
            "workout_type",             # type of workout: "standard" (default) or "alternative"
            "updated_ts",                # timestamp of the last update to this workout definition
            "updated_by"                 # member_id of the user who last updated this workout definition
            ]
    key_field="id"
    partition_value="workout"
    list_presentation = (
        {"label": "name", "value": lambda entity: entity.get("name")},
        {"label": "client", "value": assigned_client_name},
        {"label": "program", "value": lambda entity: program_name(entity) if entity.get("member_program_id") else ""},
    )
    card_presentation = {
        "title": lambda entity: entity.get("name", ""),
        "image": workout_image,
        "fields": (
            {"label": "Client", "value": member_name},
            {"label": "Program", "value": program_name},
        ),
        "actions": ("edit", "analyze", "import"),
    }

    def __init__(self, d={}):
        super().__init__(d)

class MemberWorkoutInstanceEntity (EntityObject):
    table_name="MemberWorkoutInstanceTable"   
    fields=["id", 
            'name',
            "member_id", 
            "workout_sections", 
            "started_ts", 
            "finished_ts", 
            "member_feedback",
            "scheduled_workout_event_id", 
            "adjustments_for_next_workout",
            "member_workout_def_id",          # reference to the member workout definition from which this instance was created
            "member_program_id",              # reference to the member program this workout instance is part of, if any
            "member_program_name",            # name of the member program this workout instance is part of, if any
            "next_time_workout_sections",     # this field is used to store the workout sections with adjustments for the next time already applied.
            "updated_ts",                     # timestamp of the last update to this workout definition
            "updated_by",                     # member_id of the user who last updated this workout definition
            "hide_workout"                    # flag to indicate if this workout instance should be hidden - this is useful during testing
            ]
    key_field="id"
    partition_field="member_id"
    list_presentation = (
        {"label": "name", "value": lambda entity: entity.get("name")},
        {"label": "date", "value": workout_date},
        {"label": "program", "value": lambda entity: program_name(entity) if entity.get("member_program_id") else ""},
    )
    card_presentation = {
        "title": lambda entity: entity.get("name", ""),
        "image": workout_image,
        "fields": (
            {"label": "Date", "value": workout_date},
            {"label": "Program", "value": program_name},
        ),
        "actions": ("edit",),
    }

    def __init__(self, d={}):
        super().__init__(d)


def get_exercises_from_workout(workout):
    exercises = []
    if workout:
        for s in workout['workout_sections']:
            for it in s['exercises']:
                ex = get_entity("ExerciseTable", it['id'])
                if ex:
                    ex['parameters'] = it['parameters']
                    exercises.append(ex)
    return exercises
'''
RAMP = Raise Activate Mobilize Potentiate
Raise (Body Temperature/Heart Rate): Elevate core body temperature, heart rate, respiration rate, and blood flow using low-intensity activities like jogging, skipping, or light cycling.
Activate (Key Muscles): Engage core, stabilizing, and specific muscle groups required for the session (e.g., glutes, core) to enhance stability and movement efficiency.
Mobilize (Joint Movement): Perform dynamic stretching or active mobility exercises targeting joints and movement patterns needed for the workout.
Potentiate (Performance Priming): Increase intensity to sport-specific levels, using high-intensity movements like sprinting, jumping, or shuttle runs to prime the nervous system for peak performance
'''
def map_exercise_to_sections(ex):
    physical_fitness_components = [ 'flexibility', 
                                   'core', 
                                   'mobility', 
                                   'strength', 
                                   'balance', 
                                   'cardio', 
                                   'myofascia', 
                                   'power', 
                                   'endurance'
                                   ]
    categories =  ['strength', 
                   'stretching', 
                   'mobility', 
                   'plyometrics', 
                   'strongman', 
                   'powerlifting', 
                   'olympic weightlifting', 
                   'cardio', 
                   'warmup', 
                   'core'
                   ]
    sections_map = [
                {'name':'warmup',
                 'physical_fitness_components':['flexibility', 'mobility', 'myofascia', 'balance'], 
                 'categories':['warmup', 'stretching', 'mobility']
                 },
                {'name':'ramp',
                 'physical_fitness_components':['flexibility', 'mobility', 'myofascia', 'balance'], 
                 'categories':['warmup', 'stretching', 'mobility']
                 },
                {'name':'core',
                 'physical_fitness_components':['core'], 
                 'categories':['core']
                 },
                {'name':'power',
                 'physical_fitness_components':['power'], 
                 'categories':['powerlifting', 'olympic weightlifting', 'strongman']
                 },            
                {'name':'core-power',
                 'physical_fitness_components':['power', 'core'], 
                 'categories':['powerlifting', 'olympic weightlifting', 'strongman', 'core', 'plyometrics']
                 },
                {'name':'combination',
                 'physical_fitness_components':[], 
                 'categories':[]
                 },
                {'name':'strength',
                 'physical_fitness_components':['strength'], 
                 'categories':['strength', 'powerlifting', 'olympic weightlifting', 'strongman']
                 },
                {'name':'resistance',
                 'physical_fitness_components':['strength'], 
                 'categories':['strength']
                 },
                {'name':'cardio',
                 'physical_fitness_components':['cardio', 'endurance'], 
                 'categories':['cardio']
                 }
            ]    
    # given the exercise's physical fitness components and category, use the sections map to find all the potental sections this exercise could belong to
    # collect the potential sections in a list and return the list. if there are no matches, return an empty list. 
    
    # first check the exercise's physical fitness components against the sections map
    sections_list = []
    for s in sections_map:
        if any(pfc in ex.get('physical_fitness_components', []) for pfc in s['physical_fitness_components']):
            sections_list.append(s['name'])
    
    for s in sections_map:
        if ex.get('category', '') in s['categories']:
            sections_list.append(s['name'])

    sections_list = list(set(sections_list))
    return sections_list
