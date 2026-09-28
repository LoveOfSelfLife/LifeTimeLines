import copy


def record_exercise_removal(workout_state, exercise_id):
    """Track a removed exercise id in the active workout state (deduped)."""
    removals = workout_state.setdefault('exercise_removals', [])
    if exercise_id not in removals:
        removals.append(exercise_id)
    return removals


def record_exercise_addition(workout_state, section_name, after_exercise_id, exercise_id, parameters):
    """Track an added exercise in the active workout state, anchored to the item it was inserted after."""
    additions = workout_state.setdefault('exercise_additions', [])
    additions.append({
        'section_name': section_name,
        'after_exercise_id': after_exercise_id,
        'exercise_id': exercise_id,
        'parameters': copy.deepcopy(parameters),
    })
    return additions


def apply_recorded_removals_to_definition(workout_definition, removed_exercise_ids):
    """Remove any exercises (by id) from the definition that were removed during the workout."""
    if not workout_definition or not removed_exercise_ids:
        return
    removed_ids = set(removed_exercise_ids)
    for section in workout_definition.get('workout_sections', []):
        section['exercises'] = [it for it in section.get('exercises', []) if it.get('id') not in removed_ids]


def apply_recorded_additions_to_definition(workout_definition, additions):
    """Replay recorded instance additions onto the definition, preserving insertion order."""
    if not workout_definition or not additions:
        return

    for addition in additions:
        section = next((s for s in workout_definition.get('workout_sections', [])
                         if s.get('name') == addition['section_name']), None)
        if not section:
            continue

        exercises = section.setdefault('exercises', [])
        new_item = {
            'id': addition['exercise_id'],
            'parameters': copy.deepcopy(addition['parameters']),
            'alternatives': [],
        }

        after_id = addition.get('after_exercise_id')
        insert_pos = len(exercises)
        if after_id is not None:
            for i, it in enumerate(exercises):
                if it.get('id') == after_id:
                    insert_pos = i + 1
                    break
        exercises.insert(insert_pos, new_item)
