import copy


def find_slot(workout, section_name, slot_index):
    """Locate the exercise item dict at workout['workout_sections'][section_name]['exercises'][slot_index]."""
    if not workout:
        return None
    for section in workout.get('workout_sections', []):
        if section.get('name') == section_name:
            exercises = section.get('exercises', [])
            if 0 <= slot_index < len(exercises):
                return exercises[slot_index]
            return None
    return None


def perform_exercise_swap(item, alternative_id):
    """
    Swap the given alternative into the slot occupied by `item`, in place.

    The chosen alternative is removed from item['alternatives'], the previously-active
    exercise (id + parameters) is inserted at that same position, and item['id']/item['parameters']
    become the alternative's values.

    Returns a swap-info dict, or None if the alternative id was not found.
    """
    alternatives = item.get('alternatives', [])
    for i, alt in enumerate(alternatives):
        if alt.get('id') == alternative_id:
            original_exercise_id = item.get('id')
            original_parameters = copy.deepcopy(item.get('parameters', {}))
            new_exercise_id = alt.get('id')
            new_parameters = copy.deepcopy(alt.get('parameters', {}))

            alternatives[i] = {'id': original_exercise_id, 'parameters': original_parameters}
            item['id'] = new_exercise_id
            item['parameters'] = new_parameters

            return {
                'original_exercise_id': original_exercise_id,
                'original_parameters': original_parameters,
                'new_exercise_id': new_exercise_id,
                'new_parameters': new_parameters,
            }
    return None


def record_exercise_swap(workout_state, section_name, slot_index, swap_info):
    """Track a swap for a slot in the active workout state, preserving the true original across re-swaps."""
    exercise_swaps = workout_state.setdefault('exercise_swaps', {})
    slot_key = f"{section_name}::{slot_index}"
    existing = exercise_swaps.get(slot_key)
    if existing:
        existing['new_exercise_id'] = swap_info['new_exercise_id']
        existing['new_parameters'] = swap_info['new_parameters']
    else:
        exercise_swaps[slot_key] = {
            'section_name': section_name,
            'slot_index': slot_index,
            'original_exercise_id': swap_info['original_exercise_id'],
            'original_parameters': swap_info['original_parameters'],
            'new_exercise_id': swap_info['new_exercise_id'],
            'new_parameters': swap_info['new_parameters'],
        }
    return exercise_swaps


def apply_recorded_swaps_to_definition(workout_definition, exercise_swaps):
    """Replay recorded instance swaps onto the workout definition so they persist for next time."""
    if not workout_definition or not exercise_swaps:
        return

    for swap in exercise_swaps.values():
        item = find_slot(workout_definition, swap['section_name'], swap['slot_index'])
        if not item:
            continue
        # Only apply if the slot still has the exercise the swap started from; otherwise skip to
        # avoid clobbering a definition that was edited elsewhere since the workout started.
        if item.get('id') != swap['original_exercise_id']:
            continue

        alternatives = item.setdefault('alternatives', [])
        replaced = False
        for i, alt in enumerate(alternatives):
            if alt.get('id') == swap['new_exercise_id']:
                alternatives[i] = {
                    'id': swap['original_exercise_id'],
                    'parameters': copy.deepcopy(swap['original_parameters']),
                }
                replaced = True
                break
        if not replaced:
            alternatives.append({
                'id': swap['original_exercise_id'],
                'parameters': copy.deepcopy(swap['original_parameters']),
            })

        item['id'] = swap['new_exercise_id']
        item['parameters'] = copy.deepcopy(swap['new_parameters'])
