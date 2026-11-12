"""
Reusable program objectives. An objective is a named list of rules; a program references objectives by id and
the analysis is evaluated against them on demand.

Rule fields:
  dimension  parent_pattern | pattern | muscle | pfc | laterality | equipment
  key        a single key (e.g. "PULL-VERT"), or
  keys       a list of keys, or "ALL" for every expected key of the dimension (one rule is evaluated per key)
  purpose    muscles only: strength (default) | mobility | flexibility | myofascia | any
  metric     exercises | sets | pct_sets (default: pct_sets when target is given, otherwise exercises)
  min / max  bounds on the metric
  target + tolerance   the metric should be within target +/- tolerance (default tolerance 0)
  label      optional display name
"""
import math
from datetime import datetime, timezone

from common.entity_store import EntityObject
from common.fitness.program_analysis.analyze import DEFAULT_SECONDARY_WEIGHT, expected_keys, lookup

DIMENSION_LABELS = {'parent_pattern': 'Movement family', 'pattern': 'Movement pattern', 'muscle': 'Muscle',
                    'pfc': 'Fitness component', 'laterality': 'Laterality', 'equipment': 'Equipment'}
METRICS = {'exercises': 'exercises', 'sets': 'sets', 'pct_sets': '% of sets'}
PURPOSES = ['strength', 'mobility', 'flexibility', 'myofascia', 'any']
BUILTIN_BALANCED_ID = 'builtin-balanced'


class ProgramObjectiveEntity(EntityObject):
    table_name = "ProgramObjectiveTable"
    fields = ["id", "name", "description", "rules", "secondary_muscle_weight",
              "created_by", "created_ts", "updated_ts", "updated_by"]
    key_field = "id"
    partition_value = "objective"

    def __init__(self, d={}):
        super().__init__(d)


def balanced_objective():
    """built-in profile: all patterns and muscles covered, and no movement family dominating the sets"""
    return {
        'id': BUILTIN_BALANCED_ID, 'name': 'Balanced (built-in)', 'builtin': True,
        'description': 'Every movement pattern and strengthened muscle covered at least once, '
                       'and no single movement family above 40% of the sets.',
        'secondary_muscle_weight': DEFAULT_SECONDARY_WEIGHT,
        'rules': [
            {'dimension': 'parent_pattern', 'keys': 'ALL', 'min': 1},
            {'dimension': 'pattern', 'keys': 'ALL', 'min': 1},
            {'dimension': 'muscle', 'keys': 'ALL', 'purpose': 'strength', 'min': 1},
            {'dimension': 'parent_pattern', 'keys': ['PUSH', 'PULL', 'SQUAT', 'HINGE'], 'metric': 'pct_sets', 'max': 40},
        ],
    }


def validate_rules(rules):
    """returns a list of error strings; empty when the rules are usable"""
    errors = []
    if not isinstance(rules, list) or not rules:
        return ['At least one rule is required.']
    for i, rule in enumerate(rules, 1):
        where = f'Rule {i}: '
        if not isinstance(rule, dict):
            errors.append(where + 'must be an object.')
            continue
        if rule.get('dimension') not in DIMENSION_LABELS:
            errors.append(where + 'unknown dimension.')
        if not (rule.get('key') or rule.get('keys')):
            errors.append(where + 'a key is required.')
        if rule.get('metric') and rule['metric'] not in METRICS:
            errors.append(where + 'unknown metric.')
        if rule.get('purpose') and rule['purpose'] not in PURPOSES:
            errors.append(where + 'unknown purpose.')
        if all(rule.get(f) in (None, '') for f in ('min', 'max', 'target')):
            errors.append(where + 'give a min, a max or a target.')
        for f in ('min', 'max', 'target', 'tolerance'):
            if rule.get(f) not in (None, '') and not _is_number(rule[f]):
                errors.append(where + f'{f} must be a number.')
    return errors


def _is_number(v):
    try:
        float(v)
        return True
    except (TypeError, ValueError):
        return False


def _num(v):
    return float(v) if v not in (None, '') else None


def _expand_keys(rule, include_ramp):
    keys = rule.get('keys')
    if keys == 'ALL':
        return expected_keys(include_ramp)[rule['dimension']]
    if keys:
        return list(keys)
    return [rule['key']]


def evaluate(analysis, objective):
    """
    Returns {'objective': name, 'results': [...], 'met': n, 'total': n}. Each result has the requirement, the
    actual value, status (met/under/over) and a suggested change.
    """
    results = []
    for rule in objective.get('rules') or []:
        dimension = rule['dimension']
        purpose = rule.get('purpose') or 'strength'
        target, tol = _num(rule.get('target')), _num(rule.get('tolerance')) or 0.0
        lo, hi = _num(rule.get('min')), _num(rule.get('max'))
        if target is not None:
            lo, hi = target - tol, target + tol
        metric = rule.get('metric') or ('pct_sets' if target is not None else 'exercises')
        for key in _expand_keys(rule, analysis['include_ramp']):
            cell = lookup(analysis, dimension, key, purpose)
            actual = {'exercises': cell['total_exercises'], 'sets': cell['total_sets'], 'pct_sets': cell['pct_sets']}[metric]
            status = 'under' if lo is not None and actual < lo else 'over' if hi is not None and actual > hi else 'met'
            results.append({
                'label': rule.get('label') or key,
                'dimension': dimension, 'key': key, 'purpose': purpose if dimension == 'muscle' else None,
                'metric': metric, 'min': lo, 'max': hi, 'target': target, 'actual': actual,
                'status': status, 'requirement': _requirement_text(lo, hi, target, tol, metric),
                'suggestion': _suggestion(status, key, metric, actual, lo, hi, analysis),
            })
    met = sum(1 for r in results if r['status'] == 'met')
    return {'objective': objective.get('name'), 'results': results, 'met': met, 'total': len(results)}


def _g(v):
    return f'{v:g}'


def _requirement_text(lo, hi, target, tol, metric):
    unit = METRICS[metric]
    if target is not None:
        return f'{_g(target)} ± {_g(tol)} {unit}' if tol else f'{_g(target)} {unit}'
    if lo is not None and hi is not None:
        return f'{_g(lo)}–{_g(hi)} {unit}'
    if lo is not None:
        return f'at least {_g(lo)} {unit}'
    return f'at most {_g(hi)} {unit}'


def _suggestion(status, key, metric, actual, lo, hi, analysis):
    if status == 'met':
        return ''
    if status == 'under':
        if metric == 'pct_sets':
            total = analysis['totals']['sets']
            need = max(0.0, (lo / 100.0 * total - actual / 100.0 * total) / (1 - lo / 100.0)) if lo < 100 else 0.0
            return f'Add about {math.ceil(need)} more set(s) emphasizing {key} (now {_g(actual)}% of sets).'
        return f'Add {math.ceil(lo - actual)} more {METRICS[metric]} for {key} (now {_g(actual)}).'
    if metric == 'pct_sets':
        return f'Reduce {key} to at most {_g(hi)}% of sets (now {_g(actual)}%) or add sets for other patterns.'
    return f'Remove {math.ceil(actual - hi)} {METRICS[metric]} of {key} (now {_g(actual)}).'


def new_objective_record(name, description, rules, secondary_weight, member_id, existing=None):
    now = datetime.now(timezone.utc).isoformat()
    record = dict(existing or {})
    record.update({'name': name, 'description': description, 'rules': rules,
                   'secondary_muscle_weight': secondary_weight, 'updated_ts': now, 'updated_by': member_id})
    if not existing:
        record.update({'created_by': member_id, 'created_ts': now})
    return record
