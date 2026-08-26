
from datetime import datetime, timezone

from flask import session
import json
import pytz
from common.fitness.cacher import get_cache_value, set_cache_value, delete_from_cache, get_cache_hash, get_cache_hash_field, set_cache_hash_field

# last-viewed section/exercise-index bookkeeping is stored directly in the Redis cache (not Flask's
# session) because it must not share a save-the-whole-blob-per-request cycle with the much more
# critical current_workout_instance_state - doing so caused unrelated section-switch requests to
# clobber in-flight exercise parameter edits with a stale session snapshot.

def get_last_section(member_id, workout_id):
    return get_cache_value(f"last_section_{member_id}_{workout_id}")

def set_last_section(member_id, workout_id, section_name):
    set_cache_value(f"last_section_{member_id}_{workout_id}", section_name)

def clear_last_section(member_id, workout_id):
    delete_from_cache(f"last_section_{member_id}_{workout_id}")

def get_last_exercise_index(member_id, workout_id, section_name):
    return get_cache_value(f"last_exercise_index_{member_id}_{workout_id}_{section_name}")

def set_last_exercise_index(member_id, workout_id, section_name, exercise_index):
    set_cache_value(f"last_exercise_index_{member_id}_{workout_id}_{section_name}", exercise_index)

def member_id_from_workout_instance_key(workout_instance_key):
    """workout_instance_key is (id, member_id, table_name); member_id is the partition value at index 1."""
    if isinstance(workout_instance_key, (list, tuple)) and len(workout_instance_key) > 1:
        return workout_instance_key[1]
    return None

# exercise_parameters is edited one (exercise_id, param) field at a time, on every blur - it used to
# live inside the current_workout_instance_state JSON blob, requiring a full read-modify-write of that
# whole blob per edit. Two edits fired close together (e.g. filling in several fields on a newly added
# exercise) could race and silently revert each other. Storing it as a Redis hash lets each field save
# become a single atomic HSET, with no whole-blob read-modify-write at all.

def get_exercise_parameters(member_id):
    return get_cache_hash(f"workout_exercise_params_{member_id}")

def set_exercise_parameter(member_id, exercise_id, param, value):
    entry = get_cache_hash_field(f"workout_exercise_params_{member_id}", exercise_id) or {}
    entry[param] = value
    set_cache_hash_field(f"workout_exercise_params_{member_id}", exercise_id, entry)

def clear_exercise_parameters(member_id):
    delete_from_cache(f"workout_exercise_params_{member_id}")

def initialize_active_workout_state(workout_instance_key, program_key, scheduled_workout_event_id, is_adhoc_workout=False):
    """
    Initialize the workout state in the session.
    This is called when the user starts a workout.
    """
    current_state = {
        'state': 'workout_started',
        'workout_instance_key': workout_instance_key,
        'program_key': program_key,
        'scheduled_workout_event_id': scheduled_workout_event_id,
        'workout_adjustments': {},
        'is_adhoc_workout': is_adhoc_workout,
        'exercise_parameters': {},
        'exercise_swaps': {},
        'exercise_removals': [],
        'exercise_additions': [],
        # US/Eastern local time (DST-aware), matching MemberWorkoutInstanceEntity.started_ts
        'time_workout_started': datetime.now(timezone.utc).astimezone(pytz.timezone('US/Eastern')).isoformat(),
        'keep_screen_awake': False
    }
    session['current_workout_instance_state'] = json.dumps(current_state)

def get_active_workout_state():
    """
    Retrieve the current workout state from the session.
    This is used to check if a workout is in progress.
    """
    current_state_str = session.get('current_workout_instance_state', None)
    if current_state_str:
        return json.loads(current_state_str)
    return None

def update_active_workout_state(active_workout_state):
    """
    Update the current workout state in the session.
    This is used to modify the state during the workout.
    """
    if active_workout_state:
        session['current_workout_instance_state'] = json.dumps(active_workout_state)
    else:
        clear_active_workout_state()
        
def clear_active_workout_state(member_id=None):
    """
    Clear the current workout state from the session.
    This is used when the workout is finished or canceled.
    """
    session.pop('current_workout_instance_state', None)
    if member_id:
        clear_exercise_parameters(member_id)
    # session.pop('last_section', None)  # Clear last section state as well
    # session.pop('current_workout_instance_key', None)  # Clear current workout instance key
  