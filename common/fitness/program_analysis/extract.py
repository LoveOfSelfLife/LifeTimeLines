"""Flattens a program's workouts into one row per exercise slot, ready for analysis."""
from common.fitness.exercise_analytics_db import normalize_parameters, _num

RAMP_SECTION_NAMES = {'ramp', 'warmup', 'warm-up', 'warm up'}

# exercise attributes that, when empty, are reported as data-quality gaps
REQUIRED_ATTRIBUTES = {
    'movement_categories': 'movement category',
    'physical_fitness_components': 'fitness component',
    'primaryMuscles': 'primary muscle',
}


def _as_list(value):
    if not value:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(v) for v in value if v]
    return [str(value)]


def laterality_of(exercise):
    if not exercise.get('is_unilateral'):
        return 'bilateral'
    return 'alternating' if exercise.get('is_alternating') else 'unilateral'


def is_ramp_slot(section_name, movement_categories):
    if str(section_name or '').strip().lower() in RAMP_SECTION_NAMES:
        return True
    return bool(movement_categories) and all(c == 'RAMP' for c in movement_categories)


def flatten_program(workouts, exercises_by_id):
    """
    workouts: workout definitions in program order (each has workout_sections -> exercises -> id, parameters)
    exercises_by_id: exercise id -> exercise entity (or None when it no longer exists)
    Returns (workout_infos, rows).
    """
    workout_infos = []
    rows = []
    for w_idx, workout in enumerate(workouts):
        workout_infos.append({'idx': w_idx, 'id': workout.get('id'),
                              'name': workout.get('name') or f'Workout {w_idx + 1}',
                              'purpose': workout.get('purpose')})
        for section in workout.get('workout_sections') or []:
            section_name = section.get('name')
            for item in section.get('exercises') or []:
                exercise_id = item.get('id')
                exercise = exercises_by_id.get(exercise_id)
                params = normalize_parameters(item.get('parameters'))
                sets = _num(params.get('sets'))
                time_sec = _num(params.get('time'))
                if exercise is None:
                    rows.append({'workout_idx': w_idx, 'section': section_name, 'exercise_id': exercise_id,
                                 'name': f'(missing exercise {exercise_id})', 'family': None, 'is_ramp': False,
                                 'movement_categories': [], 'primary_muscles': [], 'secondary_muscles': [],
                                 'pfcs': [], 'laterality': 'bilateral', 'equipment': [],
                                 'sets': sets or 1.0, 'sets_assumed': sets is None,
                                 'time_sec': time_sec, 'missing': ['exercise definition']})
                    continue
                categories = _as_list(exercise.get('movement_categories'))
                missing = [label for attr, label in REQUIRED_ATTRIBUTES.items()
                           if not _as_list(exercise.get(attr))]
                rows.append({
                    'workout_idx': w_idx,
                    'section': section_name,
                    'exercise_id': exercise_id,
                    'name': exercise.get('name') or exercise_id,
                    'family': (exercise.get('family') or '').strip() or None,
                    'is_ramp': is_ramp_slot(section_name, categories),
                    'movement_categories': categories,
                    'primary_muscles': _as_list(exercise.get('primaryMuscles')),
                    'secondary_muscles': _as_list(exercise.get('secondaryMuscles')),
                    'pfcs': _as_list(exercise.get('physical_fitness_components')),
                    'laterality': laterality_of(exercise),
                    'equipment': _as_list(exercise.get('equipment_list')),
                    'sets': sets or 1.0,
                    'sets_assumed': sets is None,
                    'time_sec': time_sec,
                    'missing': missing,
                })
    return workout_infos, rows


def load_program_rows(program):
    """Loads the program's standard workouts and their exercises from the entity store."""
    from common.fitness.programs import get_program_workouts

    workouts = get_program_workouts(program, workout_type='standard')
    return load_workout_rows(workouts)


def load_workout_rows(workouts):
    """Resolve exercises and flatten the supplied workout definitions."""
    from common.entity_store import EntityStore
    from common.fitness.exercise_entity import ExerciseEntity

    ids = {i.get('id') for w in workouts for s in (w.get('workout_sections') or [])
           for i in (s.get('exercises') or []) if i.get('id')}
    es = EntityStore()
    exercises_by_id = {eid: es.get_item(ExerciseEntity({'id': eid})) for eid in ids}
    return flatten_program(workouts, exercises_by_id)
