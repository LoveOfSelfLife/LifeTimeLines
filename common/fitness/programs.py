import sys
from common.fitness.entities_getter import get_filtered_entities
from common.fitness.member_program_entity import MemberProgramEntity
from datetime import datetime as dt

from common.fitness.member_workout_entity import MemberWorkoutDefinitionEntity, MemberWorkoutInstanceEntity

def get_members_current_active_program(member_id, current_date_dt=None):

    programs = get_filtered_entities(MemberProgramEntity.table_name, partition_key=member_id)
    
    # print(f"Programs for member {member_id}: {programs}")
    # find the program that is active for the current date, based on the start and end dates of the program
    if not current_date_dt:
        from datetime import datetime
        current_date_dt = datetime.now()
    
    # currrent_date_dt is a datetime object with timezone info as UTC, we need to convert it to local timezone for comparison with the program start and end dates, which are in local timezone
    import pytz
    current_date_dt = current_date_dt.astimezone(pytz.timezone('US/Eastern'))
    
    for program in programs:
        # start_date and end_date are stored as ISO format strings in the program entity, we need to convert them to datetime objects with the local timezone for comparison
        # by default, fromisoformat will set the tzinfo to null, so we need to make sure to add the local timezone to the start and end dates when converting them to datetime objects
        start_date = dt.fromisoformat(program.get('start_date')) if program.get('start_date') else None
        if start_date:
            start_date = start_date.replace(tzinfo=pytz.timezone('US/Eastern'))
            # start_date = start_date.astimezone(pytz.timezone('US/Eastern'))
        
        end_date = dt.fromisoformat(program.get('end_date')) if program.get('end_date') else None
        if end_date:
            end_date = end_date.replace(tzinfo=pytz.timezone('US/Eastern'))
            # end_date = end_date.astimezone(pytz.timezone('US/Eastern'))
        
        if start_date and end_date:
            if start_date <= current_date_dt <= end_date:
                # only return the program if it has workouts
                workouts_in_program = get_program_workouts(program, member_id)
                if workouts_in_program:
                        print(f"Found active program for member {member_id}: {program}")
                        return program
    return None

def get_program_workouts(program, member_id, workout_type=None):

    # in the new data model, all workouts are stored as MemberWorkoutDefinitionEntity entities
    member_workouts = get_filtered_entities(MemberWorkoutDefinitionEntity.table_name, partition_key=member_id)
    workouts_in_program = [w for w in member_workouts if w.get('member_program_id', None) == program.get('id', None)]
    if workout_type:
        workouts_in_program = [w for w in workouts_in_program if w.get('workout_type') == workout_type]
    # sort program_workouts by the order_index field in ascending order
    workouts_in_program.sort(key=lambda w: w.get('order_index', 0))
    return workouts_in_program


def get_last_workout_instance_for_workout(workout_def_id, member_id):
    member_workout_instances = get_filtered_entities(MemberWorkoutInstanceEntity.table_name, partition_key=member_id)
    workout_instances_for_workout = [i for i in member_workout_instances if i.get('member_workout_def_id', None) == workout_def_id]
    if not workout_instances_for_workout:
        return None
    # find the most recent instance based on the finished_ts field
    most_recent_instance = max(workout_instances_for_workout, key=lambda x: x.get('finished_ts', ''))
    return most_recent_instance

def get_next_workout_in_program(program, member_id):
    # This function should return the next workout in the program for the member
    print(f"Program: {program}, Member ID: {member_id}")

    # in the new data model, all instances of workouts are stored as MemberWorkoutInstanceEntity entities
    # every time a MemberWorkoutDefinitionEntity is done by a member, a MemberWorkoutInstanceEntity is created to track the instance of the workout
    # the MemberWorkoutInstanceEntity has a field called member_workout_def_id that references the MemberWorkoutDefinitionEntity that it is based on.
    # the next workout in the program to do is the workout that was least recently done by the member
    # for this we give each workout in the program a score based on when it was last done by the member
    # the workout with the highest score is the next workout to do
    # e.g. the last workout done gets a score of 0, the second last workout done gets a score of 1, etc.
    # if a workout was never done, it gets a score of MAX_INT
    # if there are multipe workouts with the same score, we pick one at random
    

    # first make sure that there are workouts in the program, return None if there are none
    workouts_in_program = get_program_workouts(program, member_id, workout_type='standard')
    if not workouts_in_program:
        return None  # No workouts in the program

    # next get all the workouts done by this member 
    member_workout_instances = get_filtered_entities(MemberWorkoutInstanceEntity.table_name, partition_key=member_id)

    # then filter this list to be only those that are from a workout in this program
    workout_ids_in_program = [w['id'] for w in workouts_in_program]
    workout_instances_in_program = [i for i in member_workout_instances if i.get('member_workout_def_id', None) in workout_ids_in_program]
    # if there are no workout instances in the program, return the first workout in the program
    if not workout_instances_in_program:
        return {'next_workout_key' : workouts_in_program[0].get_composite_key(), 
                'last_workout_instance_key': None,
                'adjustments_for_next_workout': {} }
        
    
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
            # workout_last_completion[workout_id] = most_recent_instance.get('finished_ts', '')
            workout_last_completion[workout_id] = {'finished_ts':most_recent_instance.get('finished_ts', ''), 
                                                    'adjustments': most_recent_instance.get('adjustments_for_next_workout', {}),
                                                    'instance_key': most_recent_instance.get_composite_key() }
        else:
            # Never done - use empty string (will sort first)
            workout_last_completion[workout_id] = {'finished_ts': '', 'instance_key': None, 'instance': None}

    # Find the workout with the oldest "least recent completion"
    # Workouts never done (empty string) will be chosen first
    least_recent_workout_id = min(workout_last_completion, key=lambda k: workout_last_completion[k]['finished_ts'])
    next_workout = [w for w in workouts_in_program if w['id'] == least_recent_workout_id][0]
    last_workout_intance_key = workout_last_completion[least_recent_workout_id].get('instance_key', None)
    last_workout_adjustments = workout_last_completion[least_recent_workout_id].get('adjustments_for_next_workout', {})
    print(f"Next workout for member {member_id} in program {program.get('id')}: {next_workout}, last instance key: {last_workout_intance_key}")

    return {'next_workout_key' : next_workout.get_composite_key(), 
            'last_workout_instance_key': last_workout_intance_key, 
            'adjustments_for_next_workout': last_workout_adjustments}


def get_workouts_from_program(program):
    # in the 1.0 data model, the workouts are stored as embedded objects in the program
    # in the 2.0 data model, the workouts are stored as separate entities in the MemberWorkoutDefinitionTable, where 
    # those entities have a member_program_id field that references the program they belong to
    workouts = get_program_workouts(program, program['member_id'])
    workouts = sorted(workouts, key=lambda x: x.get('order_index', 0))
    return workouts
