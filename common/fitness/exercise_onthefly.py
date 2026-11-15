import copy
import logging


logger = logging.getLogger(__name__)


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


def record_alternative_changes(workout_state, section_name, slot_index, item):
    changes = workout_state.setdefault('alternative_changes', [])
    change = next((entry for entry in changes
                   if entry['section_name'] == section_name and entry['slot_index'] == slot_index), None)
    if change is None:
        swaps = workout_state.get('exercise_swaps', {})
        swap = swaps.get(f'{section_name}::{slot_index}', {})
        if swap.get('new_exercise_id') != item['id']:
            matches = [entry for entry in swaps.values()
                       if entry.get('section_name') == section_name and entry.get('new_exercise_id') == item['id']]
            swap = matches[0] if len(matches) == 1 else {}
        change = {
            'section_name': section_name,
            'slot_index': slot_index,
            'original_exercise_id': swap.get('original_exercise_id', item['id']),
        }
        changes.append(change)
    change['item'] = copy.deepcopy(item)


def shift_alternative_changes(workout_state, section_name, slot_index, inserted):
    changes = workout_state.get('alternative_changes', [])
    for change in list(changes):
        if change['section_name'] != section_name:
            continue
        if not inserted and change['slot_index'] == slot_index:
            changes.remove(change)
        elif change['slot_index'] > slot_index:
            change['slot_index'] += 1 if inserted else -1


def apply_recorded_alternative_changes(workout_definition, changes):
    for change in changes:
        section = next((section for section in workout_definition.get('workout_sections', [])
                        if section.get('name') == change['section_name']), None)
        if not section:
            logger.warning("Cannot apply alternative changes: section %s not found", change['section_name'])
            continue
        exercises = section.get('exercises', [])
        index = change['slot_index']
        if not 0 <= index < len(exercises):
            logger.warning("Cannot apply alternative changes: slot %s in section %s not found",
                           index, change['section_name'])
            continue
        target = exercises[index]
        item = change['item']
        if target.get('id') not in (change['original_exercise_id'], item.get('id')):
            logger.warning("Cannot apply alternative changes: exercise at slot %s in section %s has changed",
                           index, change['section_name'])
            continue
        if target.get('id') != item.get('id'):
            target['id'] = item['id']
            target['parameters'] = copy.deepcopy(item.get('parameters', {}))
        target['alternatives'] = copy.deepcopy(item.get('alternatives', []))


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
