
from flask import session
import json

def initialize_active_workout_state(workout_instance_key, program_key, scheduled_workout_event_id):
    """
    Initialize the workout state in the session.
    This is called when the user starts a workout.
    """
    current_state = {
        'state': 'workout_started',
        'workout_instance_key': workout_instance_key,
        'program_key': program_key,
        'scheduled_workout_event_id': scheduled_workout_event_id,
        'workout_adjustments': {}
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
        
def clear_active_workout_state():
    """
    Clear the current workout state from the session.
    This is used when the workout is finished or canceled.
    """
    session.pop('current_workout_instance_state', None)
    # session.pop('last_section', None)  # Clear last section state as well
    # session.pop('current_workout_instance_key', None)  # Clear current workout instance key
  