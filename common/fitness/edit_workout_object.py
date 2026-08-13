from common.fitness.cacher import get_cache_value, set_cache_value
from flask import redirect, url_for

def bring_up_workouts_builder(workout_obj):
    workout_editor_context = get_cache_value('workout_editor_context') or {}
    # if this workout edit action was initiated from the program builder, 
    # then the workout_editor_context will have an 'editing_program_workout' key that is set to the workout object that is being edited as part of the program builder flow.
    # 
    set_cache_value('current_workout', workout_obj)
    if workout_editor_context.get('editing_program_workout', None) is not None:
        return redirect(url_for('workouts.builder', workout_id=workout_obj['id'], editing_program_workout=True))
    else:
        return redirect(url_for('workouts.builder', workout_id=workout_obj['id']))
    