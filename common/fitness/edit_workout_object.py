from common.fitness.cacher import get_cache_value, set_cache_value


from flask import redirect, url_for


def edit_workout_object(workout_obj):
    workout_editor_context = get_cache_value('workout_editor_context') or {}
    # editing_program_workout will be set to the ID of the workout that is part of a program 
    # if this workout edit action was initiated from the 
    # program builder while editing a workout that is part of a member program. 
    if workout_editor_context.get('editing_program_workout', None) is not None:
        program_workout_obj = workout_editor_context['editing_program_workout']
        set_cache_value('current_workout', program_workout_obj)
        return redirect(url_for('workouts.builder', workout_id=program_workout_obj['id'], editing_program_workout=True))
    else:
        set_cache_value('current_workout', workout_obj)
        return redirect(url_for('workouts.builder', workout_id=workout_obj['id']))
    