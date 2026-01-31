import sys
from common.entity_store import EntityStore
from common.fitness.entities_getter import get_list_of_entities

from common.fitness.entity_constants import DATAMODEL_VERSION, PROGRAM_ENTITY_NAME
from common.fitness.program_entity import ProgramEntity
from common.fitness.member_program_entity import MemberProgramEntity
from datetime import datetime as dt

def get_members_current_active_program(member_id, current_date_dt=None):

    if DATAMODEL_VERSION == 2:
        programs = get_list_of_entities(MemberProgramEntity.table_name, partition_key=member_id)
    else:
        programs = get_list_of_entities(ProgramEntity.table_name, partition_key=member_id)
    
    print(f"Programs for member {member_id}: {programs}")
    # find the program that is active for the current date, based on the start and end dates of the program
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
                workouts_in_program = get_workouts_in_program(program, member_id)
                if workouts_in_program:
                        print(f"Found active program for member {member_id}: {program}")
                        return program
    return None

def get_workouts_in_program(program, member_id):
    if DATAMODEL_VERSION == 2:
        # in the new data model, all workouts are stored as MemberWorkoutDefinitionEntity entities
        member_workouts = get_list_of_entities("MemberWorkoutDefinitionTable", partition_key=member_id)
        workouts_in_program = [w for w in member_workouts if w.get('member_program_id', None) == program.get('id', None)]
        return workouts_in_program
    else:
        return program.get('workouts', [])

def get_next_workout_in_program(program, member_id):
    # This function should return the next workout in the program for the member
    print(f"Program: {program}, Member ID: {member_id}")
    if DATAMODEL_VERSION == 2:
        # in the new data model, all instances of workouts are stored as MemberWorkoutInstanceEntity entities
        # every time a MemberWorkoutDefinitionEntity is done by a member, a MemberWorkoutInstanceEntity is created to track the instance of the workout
        # the MemberWorkoutInstanceEntity has a field called member_workout_def_id that references the MemberWorkoutDefinitionEntity that it is based on.
        # the next workout in the program to do is the workout that was least recently done by the member
        # for this we give each workout in the program a score based on when it was last done by the member
        # the workout with the highest score is the next workout to do
        # e.g. the last workout done gets a score of 0, the second last workout done gets a score of 1, etc.
        # if a workout was never done, it gets a score of MAX_INT
        # if there are multipe workouts with the same score, we pick one at random
        #

        # first make sure that there are workouts in the program, return None if there are none
        workouts_in_program = get_workouts_in_program(program, member_id)
        if not workouts_in_program:
            return None  # No workouts in the program

        # next get all the workouts done by this member 
        member_workout_instances = get_list_of_entities("MemberWorkoutInstanceTable", partition_key=member_id)

        # then filter this list to be only those that are from a workout in this program
        workout_ids_in_program = [w['id'] for w in workouts_in_program]
        workout_instances_in_program = [i for i in member_workout_instances if i.get('member_workout_def_id', None) in workout_ids_in_program]
        # if there are no workout instances in the program, return the first workout in the program
        if not workout_instances_in_program:
            return workouts_in_program[0]        
       
        # For each workout, find when it was most recently completed (or never)
        workout_last_completion = {}
        for workout in workouts_in_program:
            workout_id = workout['id']
            # Find all instances of this specific workout
            instances_of_this_workout = [i for i in workout_instances_in_program 
                                       if i.get('member_workout_def_id') == workout_id]
            
            if instances_of_this_workout:
                # Get the most recent completion timestamp for this workout
                most_recent_instance = max(instances_of_this_workout, 
                                         key=lambda x: x.get('finished_ts', ''))
                workout_last_completion[workout_id] = most_recent_instance.get('finished_ts', '')
            else:
                # Never done - use empty string (will sort first)
                workout_last_completion[workout_id] = ''

        # Find the workout with the oldest "most recent completion"
        # Workouts never done (empty string) will be chosen first
        least_recent_workout_id = min(workout_last_completion, key=workout_last_completion.get)
        next_workout = [w for w in workouts_in_program if w['id'] == least_recent_workout_id][0]
        return next_workout
    else:
        return get_next_workout_in_program_v1(program, member_id)

def get_next_workout_in_program_v1(program, member_id):
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
