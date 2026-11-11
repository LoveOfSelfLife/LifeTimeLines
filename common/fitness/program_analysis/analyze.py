"""
Pure-python analysis of a flattened program (see extract.py): movement patterns, muscles by purpose, fitness
components, laterality, cardio/balance, repeats, per-workout gaps and data-quality flags.

Every table maps key -> {'exercises': [per workout], 'sets': [per workout], 'total_exercises', 'total_sets',
'pct_sets'}; percentages are always the share of the scoped program's sets.
"""
from common.fitness.exercise_entity import MOVEMENT_CATEGORIES, MUSCLES, PHYSICAL_FITNESS_COMPONENTS

DEFAULT_SECONDARY_WEIGHT = 0.5

PARENT_PATTERNS = ['PUSH', 'PULL', 'SQUAT', 'HINGE', 'CORE']
SPECIFIC_PATTERNS = [c for c in MOVEMENT_CATEGORIES if '-' in c]
LATERALITIES = ['bilateral', 'unilateral', 'alternating']

# muscle credit is split by the purpose the exercise serves, so shoulder mobility never counts as shoulder strength
BUCKETS = ['strength', 'mobility', 'flexibility', 'myofascia', 'other', 'unspecified']
PFC_BUCKET = {'strength': 'strength', 'power': 'strength', 'endurance': 'strength', 'core': 'strength',
              'mobility': 'mobility', 'flexibility': 'flexibility', 'myofascia': 'myofascia',
              'balance': 'other', 'cardio': 'other'}

DIMENSIONS = ['parent_pattern', 'pattern', 'muscle', 'pfc', 'laterality', 'equipment']


def parent_pattern(category):
    return category.split('-')[0]


def _empty_cell(n):
    return {'exercises': [0.0] * n, 'sets': [0.0] * n}


def _add(table, key, w_idx, n, exercises, sets):
    cell = table.setdefault(key, _empty_cell(n))
    cell['exercises'][w_idx] += exercises
    cell['sets'][w_idx] += sets


def _finalize(table, expected, n, total_sets):
    for key in expected:
        table.setdefault(key, _empty_cell(n))
    for cell in table.values():
        cell['total_exercises'] = round(sum(cell['exercises']), 4)
        cell['total_sets'] = round(sum(cell['sets']), 4)
        cell['pct_sets'] = round(100.0 * cell['total_sets'] / total_sets, 2) if total_sets else 0.0
    return table


def expected_keys(include_ramp=False):
    parents = PARENT_PATTERNS + (['RAMP'] if include_ramp else [])
    return {'parent_pattern': parents, 'pattern': list(SPECIFIC_PATTERNS), 'muscle': list(MUSCLES),
            'pfc': list(PHYSICAL_FITNESS_COMPONENTS), 'laterality': list(LATERALITIES), 'equipment': []}


def _muscle_weights(row, secondary_weight):
    weights = {m: secondary_weight for m in row['secondary_muscles']}
    for m in row['primary_muscles']:
        weights[m] = 1.0
    return weights


def _buckets_of(row):
    buckets = {PFC_BUCKET[p] for p in row['pfcs'] if p in PFC_BUCKET}
    return buckets or {'unspecified'}


def analyze(workout_infos, rows, include_ramp=False, secondary_weight=DEFAULT_SECONDARY_WEIGHT):
    n = len(workout_infos)
    scoped = [r for r in rows if include_ramp or not r['is_ramp']]
    expected = expected_keys(include_ramp)

    tables = {d: {} for d in DIMENSIONS if d != 'muscle'}
    muscle_tables = {b: {} for b in BUCKETS}
    workouts = [dict(w, exercises=0, sets=0.0) for w in workout_infos]
    cardio_seconds = [0.0] * n

    for r in scoped:
        w, sets = r['workout_idx'], r['sets']
        workouts[w]['exercises'] += 1
        workouts[w]['sets'] += sets
        for c in set(r['movement_categories']):
            _add(tables['pattern'], c, w, n, 1, sets)
        for p in {parent_pattern(c) for c in r['movement_categories']}:
            _add(tables['parent_pattern'], p, w, n, 1, sets)
        for p in set(r['pfcs']):
            _add(tables['pfc'], p, w, n, 1, sets)
        _add(tables['laterality'], r['laterality'], w, n, 1, sets)
        for e in set(r['equipment']) or {'none'}:
            _add(tables['equipment'], e, w, n, 1, sets)
        weights = _muscle_weights(r, secondary_weight)
        for bucket in _buckets_of(r):
            for m, weight in weights.items():
                _add(muscle_tables[bucket], m, w, n, weight, weight * sets)
        if 'cardio' in r['pfcs'] and r['time_sec']:
            cardio_seconds[w] += r['time_sec'] * sets

    total_sets = sum(w['sets'] for w in workouts)
    for w in workouts:
        w['sets'] = round(w['sets'], 4)
    for dim, table in tables.items():
        _finalize(table, expected[dim], n, total_sets)
    for table in muscle_tables.values():
        _finalize(table, expected['muscle'], n, total_sets)
    tables['muscle'] = muscle_tables

    result = {
        'include_ramp': include_ramp,
        'secondary_weight': secondary_weight,
        'workouts': workouts,
        'totals': {'exercises': len(scoped), 'sets': round(total_sets, 4)},
        'tables': tables,
        'expected': expected,
        'cardio': _cardio_summary(tables['pfc'], cardio_seconds),
        'balance': _cell_summary(tables['pfc'].get('balance')),
        'ratios': _ratios(tables),
        'repeats': _repeats(scoped, workout_infos),
        'data_quality': _data_quality(scoped, workout_infos),
    }
    result['uncovered'] = _uncovered(result)
    result['gaps'] = _gaps(result)
    result['essence'] = _essence(result)
    return result


def lookup(analysis, dimension, key, purpose='strength'):
    """the table cell for a dimension/key (zero cell when absent); purpose only matters for muscles"""
    n = len(analysis['workouts'])
    table = analysis['tables'][dimension]
    if dimension == 'muscle':
        if purpose == 'any':
            return _combined_muscle_cell(table, key, n, analysis['totals']['sets'])
        table = table[purpose]
    return table.get(key) or _finalize({}, [key], n, analysis['totals']['sets'])[key]


def _combined_muscle_cell(muscle_tables, key, n, total_sets):
    combined = _empty_cell(n)
    for table in muscle_tables.values():
        cell = table.get(key)
        if cell:
            for i in range(n):
                combined['exercises'][i] += cell['exercises'][i]
                combined['sets'][i] += cell['sets'][i]
    return _finalize({key: combined}, [], n, total_sets)[key]


def _cell_summary(cell):
    if not cell:
        return {'exercises': 0, 'sets': 0.0, 'per_workout': []}
    return {'exercises': cell['total_exercises'], 'sets': cell['total_sets'], 'per_workout': cell['exercises']}


def _cardio_summary(pfc_table, cardio_seconds):
    summary = _cell_summary(pfc_table.get('cardio'))
    summary['minutes_per_workout'] = [round(s / 60.0, 1) for s in cardio_seconds]
    summary['minutes'] = round(sum(cardio_seconds) / 60.0, 1)
    return summary


def _ratio(a, b):
    return round(a / b, 2) if b else None


def _ratios(tables):
    parent = tables['parent_pattern']
    strength = tables['muscle']['strength']

    def sets_of(table, key):
        return table[key]['total_sets'] if key in table else 0.0

    push, pull = sets_of(parent, 'PUSH'), sets_of(parent, 'PULL')
    quads, hams = sets_of(strength, 'quadriceps'), sets_of(strength, 'hamstrings')
    return {'push_pull': {'push': push, 'pull': pull, 'ratio': _ratio(push, pull)},
            'quadriceps_hamstrings': {'quadriceps': quads, 'hamstrings': hams, 'ratio': _ratio(quads, hams)}}


def _repeats(scoped, workout_infos):
    names = {w['idx']: w['name'] for w in workout_infos}
    by_exercise, by_family = {}, {}
    for r in scoped:
        e = by_exercise.setdefault(r['exercise_id'], {'name': r['name'], 'slots': 0, 'workouts': set()})
        e['slots'] += 1
        e['workouts'].add(r['workout_idx'])
        if r['family']:
            f = by_family.setdefault(r['family'], {'exercises': set(), 'slots': 0, 'workouts': set()})
            f['exercises'].add(r['name'])
            f['slots'] += 1
            f['workouts'].add(r['workout_idx'])

    def label(idxs):
        return [names[i] for i in sorted(idxs)]

    exercises = [{'name': e['name'], 'slots': e['slots'], 'workouts': label(e['workouts'])}
                 for e in by_exercise.values() if e['slots'] > 1]
    families = [{'family': k, 'exercises': sorted(f['exercises']), 'slots': f['slots'], 'workouts': label(f['workouts'])}
                for k, f in by_family.items() if f['slots'] > 1]
    return {'exercises': sorted(exercises, key=lambda x: -x['slots']),
            'families': sorted(families, key=lambda x: -x['slots'])}


def _data_quality(scoped, workout_infos):
    names = {w['idx']: w['name'] for w in workout_infos}
    missing = [{'workout': names[r['workout_idx']], 'exercise_id': r['exercise_id'], 'name': r['name'],
                'missing': r['missing']} for r in scoped if r['missing']]
    assumed = [{'workout': names[r['workout_idx']], 'exercise_id': r['exercise_id'], 'name': r['name']}
               for r in scoped if r['sets_assumed']]
    return {'missing_attributes': missing, 'assumed_sets': assumed}


def _uncovered(analysis):
    t = analysis['tables']
    return {'parent_pattern': [k for k in analysis['expected']['parent_pattern'] if not t['parent_pattern'][k]['total_exercises']],
            'pattern': [k for k in analysis['expected']['pattern'] if not t['pattern'][k]['total_exercises']],
            'muscle': [k for k in analysis['expected']['muscle'] if not t['muscle']['strength'][k]['total_exercises']]}


def _gaps(analysis):
    """per workout: what it lacks, flagged when no workout in the program covers it either"""
    t = analysis['tables']
    gaps = []
    for w in analysis['workouts']:
        i = w['idx']

        def missing(table, keys):
            return [{'key': k, 'program_wide': not table[k]['total_exercises']}
                    for k in keys if not table[k]['exercises'][i]]

        gaps.append({'idx': i, 'name': w['name'],
                     'parent_pattern': missing(t['parent_pattern'], analysis['expected']['parent_pattern']),
                     'pattern': missing(t['pattern'], analysis['expected']['pattern']),
                     'muscle': missing(t['muscle']['strength'], analysis['expected']['muscle'])})
    return gaps


def _top(table, i, limit, key_filter=None):
    items = [(k, c['exercises'][i]) for k, c in table.items() if c['exercises'][i] > 0 and (not key_filter or key_filter(k))]
    return sorted(items, key=lambda kv: (-kv[1], kv[0]))[:limit]


def _fmt_count(v):
    return f'{v:g}'


def _essence(analysis):
    """a one-line summary of each workout: patterns | muscles | components | laterality"""
    t = analysis['tables']
    out = []
    for w in analysis['workouts']:
        i = w['idx']
        patterns = _top(t['pattern'], i, 5)
        muscles = _top(t['muscle']['strength'], i, 4)
        pfcs = _top(t['pfc'], i, 6)
        lat = t['laterality']
        uni = lat['unilateral']['exercises'][i] + lat['alternating']['exercises'][i]
        uni_pct = round(100.0 * uni / w['exercises']) if w['exercises'] else 0
        parts = [', '.join(f'{k} ×{_fmt_count(v)}' for k, v in patterns) or 'no movement patterns',
                 ', '.join(k for k, _ in muscles) or 'no strengthened muscles',
                 ', '.join(k for k, _ in pfcs) or 'no fitness components',
                 f'{uni_pct}% unilateral']
        out.append({'idx': i, 'name': w['name'], 'patterns': patterns, 'muscles': muscles, 'pfcs': pfcs,
                    'unilateral_pct': uni_pct, 'text': ' | '.join(parts)})
    return out
