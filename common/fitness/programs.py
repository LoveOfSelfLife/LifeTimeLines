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
        start_date = dt.fromisoformat(program.get('start_date'))if program.get('start_date') else None
        end_date = dt.fromisoformat(program.get('end_date')) if program.get('end_date') else None
        if start_date and end_date:
            if start_date <= current_date_dt <= end_date:
                # only return the program if it has workouts
                if program.get('workouts', []):
                    print(f"Found active program for member {member_id}: {program}")
                    return program
    return None

def get_next_workout_in_program(program, member_id):
    # This function should return the next workout in the program for the member
    print(f"Program: {program}, Member ID: {member_id}")
    # program workout_instances is a list of the workouts that have already been finished by the member.
    # we find the last workout that was finished, then look at the program workout instance to
    # identify the workout in the ProgramWorkout table that wsa done last. 
    # then this function will return the next workout in the program after the last one that was done.
    # if we reach teh end of the list, then return the first workout in the program.
    workout_instances = program.get('workout_instances', [])
    if workout_instances:
        # Get the last workout instance
        last_workout_instance = workout_instances[-1]  # Assuming the last one is the most recent
        program_workout_instance_key = last_workout_instance.get('program_workout_instance_key')
        # the program workout will be the 2nd item in the instance key list
        last_program_workout = program_workout_instance_key[1] if len(program_workout_instance_key) > 1 else None
        if not last_program_workout:
            return None
        # Get the program workout entity using the key
        program_workouts = program.get('workouts', [])
        if not program_workouts:
            return None  # No workouts in the program
        workouts_list = [e['id'] for e in program_workouts]
        next_workout_index = find_index_of_element_after_target(workouts_list, last_program_workout)
        if next_workout_index == -1:
            next_workout_index = 0
        next_workout_key = tuple(program_workouts[next_workout_index]['key'])
        # now we need to look through the workout instances in reverse, starting with the last instance, 
        # in order to find the last workout instance that was done that had a workout key that matches the next workout key.
        last_workout_instance_key = None
        adjustments_for_next_workout = {}
        for instance in reversed(workout_instances):
            pikey = instance.get('program_workout_instance_key') 
            if pikey[1] == next_workout_key[0]:
                last_workout_instance_key = pikey
                adjustments_for_next_workout = instance.get('adjustments_for_next_workout', {})
                break
        return { "next_workout_key": next_workout_key, "last_workout_instance_key": last_workout_instance_key, "adjustments_for_next_workout": adjustments_for_next_workout }
    else:
        # otherwise we just use the first workout in the program
        program_workouts = program.get('workouts', [])
        if not program_workouts:
            return None  # No workouts in the program
        return { "next_workout_key": tuple(program_workouts[0]['key']), "last_workout_instance": None, "adjustments_for_next_workout": {} }
    
def find_index_of_element_after_target(elements, target):
    try:
        index = elements.index(target)
        if index + 1 < len(elements):
            return index + 1
        else:
            return 0
    except ValueError:
        return -1
