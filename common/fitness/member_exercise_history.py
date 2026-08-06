from common.entity_store import EntityObject, EntityStore
from common.fitness.exercise_entity import ExerciseEntity

class MemberPerformsExerciseEntity (EntityObject):
    """
    This entity represents a member performing an exercise.  It is used to generate a unique ID for the exercise instance, which is then used as the partition key in the MemberExerciseEventHistoryEntity.
    """
    table_name="MemberPerformsExerciseTable"
    fields=["member_id", "exercise_id", "exercise_instance_partition_key"]
    key_field="exercise_id"
    partition_field="member_id"

    def __init__(self, d={}):
        super().__init__(d)
        self['exercise_instance_partition_key'] = f"{self.get('member_id')}_{self.get('exercise_id')}"

class MemberExerciseEventHistoryEntity (EntityObject):
    """
    This entity represents an exercise event performed by a member.  It is used to store the history of exercises performed by members.  The partition key is the exercise_instance_partition_key generated in the MemberPerformsExerciseEntity, which represents a member performing an exercise.  The event_id is represents the specific instance of a member performing an exercise, or in our case, a workout, so we use 
    the date & time of the workout as the event_id to differentiate between different instances of a member performing the same exercise in different workouts.
    """
    table_name="MemberExerciseEventHistoryTable"
    fields=["event_id", "exercise_id", "exercise_instance_partition_key", "member_id", "member_workout_instance_id", "member_program_instance_id", "date_time", "sets", "reps", "weight", "weight_unit", "time", "tempo"]
    key_field="event_id"
    partition_field="exercise_instance_partition_key"

    def __init__(self, d={}):
        super().__init__(d)



def extract_and_load_exercise_events_from_workout_instance(workout_instance):
    """
    a function that when given an instance of MemberWorkoutInstanceEntity.
    it will extract the information needed to populate the MemberPerformsExerciseTable
    as well as the MemberExerciseEventHistoryTable
    """
    es = EntityStore()
    exercise_events = []
    exercises = workout_instance.get('workout_sections', [])
    for section in exercises:
        for exercise in section.get('exercises', []):
            exercise_id = exercise.get('id', None)
            member_id = workout_instance.get('member_id', None)
            if exercise_id and member_id:
                performs_entity = get_member_performs_exercise_entity(exercise_id, member_id)
                exercise_instance_partition_key = performs_entity['exercise_instance_partition_key']

                if workout_instance.get('started_ts', None):  # only create an event if the workout has a start time, which indicates that the workout was actually performed
                    event_entity = MemberExerciseEventHistoryEntity({
                        'event_id': workout_instance.get('started_ts', None),  # using the workout start time as the event_id to differentiate between different instances of performing the same exercise
                        'exercise_id': exercise_id,
                        'exercise_instance_partition_key': exercise_instance_partition_key,
                        'member_id': member_id,
                        'member_workout_instance_id': workout_instance.get('id', None),
                        'member_program_instance_id': workout_instance.get('member_program_id', None),
                        'date_time': workout_instance.get('started_ts', None),
                        'sets': exercise.get('parameters', {}).get('sets', None),
                        'reps': exercise.get('parameters', {}).get('reps', None),
                        'weight': exercise.get('parameters', {}).get('weight', None),
                        'weight_unit': exercise.get('parameters', {}).get('weight_unit', None),
                        'time': exercise.get('parameters', {}).get('time', None),
                        'tempo': exercise.get('parameters', {}).get('tempo', None)
                    })
                    es.upsert_item(event_entity)



def get_member_performs_exercise_entity(exercise_id, member_id):
    """
    before creating a new entity, check if the member already has performed this exercise before by trying to get the entity with the same exercise_id and member_id.  If it exists, it will return the existing entity with the same partition key, if not it will create a new entity with a new partition key.  This way we can group all events for the same member performing the same exercise under the same partition key in the MemberExerciseEventHistoryTable.
    """
    es = EntityStore()
    performs_entity = MemberPerformsExerciseEntity({'exercise_id': exercise_id, 'member_id': member_id} )
    if e := es.get_item(performs_entity):
        return e
    else:
        es.upsert_item(performs_entity)
    return performs_entity

def get_exercise_history_for_member(member_id, exercise_id):
    """
    a function that when given a member_id and exercise_id, it will return the history of events for that member performing that exercise by querying the MemberExerciseEventHistoryTable with the partition key generated from the member_id and exercise_id.
    """
    es = EntityStore()
    exercise_instance_partition_key = f"{member_id}_{exercise_id}"
    events = es.list_items(MemberExerciseEventHistoryEntity({'exercise_instance_partition_key': exercise_instance_partition_key}))
    exercise_entity = es.get_item(ExerciseEntity({'id': exercise_id}))
    exercise_history = format_exercise_history(events, exercise_entity)
    return exercise_history

def format_exercise_history(events, exercise_entity):
    """function that uses infor from the exercise_entity to better format a list of prior exercises performed by a member
    for example, if the exercise does not use any equipment, then we can omit the weight and weight unit from the result
    or if the exercise is time based, then we can omit reps & weight and just include sets and time, etc.
    """
    exercise_name = exercise_entity.get('name', None)
    equipment = exercise_entity.get('equipment', None)
    exercise_type = exercise_entity.get('type', None)
    formatted_events = []
    for event in events:
        formatted_event = {}
        formatted_event['exercise_id'] = exercise_entity.get('id', None)
        formatted_event['date_time'] = event.get('date_time', None)
        formatted_event['sets'] = event.get('sets', None)
        formatted_event['reps'] = event.get('reps', None)
        formatted_event['weight'] = event.get('weight', None)
        formatted_event['weight_unit'] = event.get('weight_unit', None)
        formatted_event['time'] = event.get('time', None)
        formatted_event['tempo'] = event.get('tempo', None)
        formatted_events.append(formatted_event)
    events = {
        'exercise_name': exercise_name,
        'equipment': equipment,
        'exercise_type': exercise_type,
        'events': formatted_events
    }   
    # return the formated_events in reverse chronological order (most recent first)
    sorted_events = sorted(formatted_events, key=lambda x: x['date_time'], reverse=True)
    return sorted_events
