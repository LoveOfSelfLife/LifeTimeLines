from common.entity_store import EntityStore
from common.fitness.entities_getter import get_list_of_entities
from common.fitness.program_entity import ProgramEntity
from datetime import datetime as dt

def get_members_program(member_id, current_date_dt=None):
    programs = get_list_of_entities(ProgramEntity.table_name, partition_key=member_id)
    print(f"Programs for member {member_id}: {programs}")
    # fine the program that is active for the current date, baased on the start and end dates of the program
    if not current_date_dt:
        from datetime import datetime
        current_date_dt = datetime.now()
    # current_date_dt is a datetime object, but start_date and end_date are likely strings, so we need to convert them to datetime objects
    
    for program in programs:
        start_date = dt.fromisoformat(program.get('start_date'))
        end_date = dt.fromisoformat(program.get('end_date'))
        if start_date and end_date:
            if start_date <= current_date_dt <= end_date:
                return program
    return None

def get_next_workout_in_program(program, member_id):
    # This function should return the next workout in the program for the member
    print(f"Program: {program}, Member ID: {member_id}")
    if len(program.get('workouts', [])) >= 1:
        wk = program['workouts'][0]  # Assuming the first workout is the next one
        es = EntityStore()
        workout = es.get_item_by_composite_key2(wk.get('key'))
        return workout
    return None 

