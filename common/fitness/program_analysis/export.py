"""Export of a program analysis: flat tables for Excel/CSV, and the JSON form."""
import csv
import io
import json

from common.fitness.program_analysis.analyze import BUCKETS

ROW_COLUMNS = ['workout', 'section', 'exercise', 'family', 'is_ramp', 'sets', 'sets_assumed', 'movement_categories',
               'primary_muscles', 'secondary_muscles', 'fitness_components', 'laterality', 'equipment', 'missing']


def raw_rows(workout_infos, rows):
    names = {w['idx']: w['name'] for w in workout_infos}
    return [[names[r['workout_idx']], r['section'], r['name'], r['family'], r['is_ramp'], r['sets'], r['sets_assumed'],
             ', '.join(r['movement_categories']), ', '.join(r['primary_muscles']), ', '.join(r['secondary_muscles']),
             ', '.join(r['pfcs']), r['laterality'], ', '.join(r['equipment']), ', '.join(r['missing'])] for r in rows]


def _table_sheet(analysis, table, label):
    names = [w['name'] for w in analysis['workouts']]
    header = [label] + [f'{n} (sets)' for n in names] + ['Total exercises', 'Total sets', '% of sets']
    body = [[k] + c['sets'] + [c['total_exercises'], c['total_sets'], c['pct_sets']] for k, c in table.items()]
    return [header] + sorted(body, key=lambda r: -r[-2])


def sheets(analysis, workout_infos, rows, evaluation=None, scope='program'):
    """sheet name -> list of rows (first row is the header)"""
    t = analysis['tables']
    out = {
        'Summary': [['Workout', 'Exercises', 'Sets', 'Essence']] +
                   [[w['name'], w['exercises'], w['sets'], e['text']] for w, e in zip(analysis['workouts'], analysis['essence'])],
        'Movement patterns': _table_sheet(analysis, t['pattern'], 'Pattern'),
        'Movement families': _table_sheet(analysis, t['parent_pattern'], 'Family'),
        'Fitness components': _table_sheet(analysis, t['pfc'], 'Component'),
        'Laterality': _table_sheet(analysis, t['laterality'], 'Laterality'),
        'Equipment': _table_sheet(analysis, t['equipment'], 'Equipment'),
    }
    for bucket in BUCKETS:
        if any(c['total_sets'] for c in t['muscle'][bucket].values()):
            out[f'Muscles - {bucket}'] = _table_sheet(analysis, t['muscle'][bucket], 'Muscle')
    out['Gaps'] = [['Workout', 'Kind', 'Missing', f'Missing from whole {scope}']] + [
        [g['name'], kind, m['key'], m['program_wide']] for g in analysis['gaps']
        for kind in ('parent_pattern', 'pattern', 'muscle') for m in g[kind]]
    out['Repeats'] = [['Kind', 'Name', 'Slots', 'Workouts']] + \
        [['exercise', r['name'], r['slots'], ', '.join(r['workouts'])] for r in analysis['repeats']['exercises']] + \
        [['family', r['family'], r['slots'], ', '.join(r['workouts'])] for r in analysis['repeats']['families']]
    dq = analysis['data_quality']
    out['Data quality'] = [['Workout', 'Exercise', 'Issue']] + \
        [[m['workout'], m['name'], 'missing: ' + ', '.join(m['missing'])] for m in dq['missing_attributes']] + \
        [[m['workout'], m['name'], 'no set count, 1 assumed'] for m in dq['assumed_sets']]
    if evaluation:
        out['Objective'] = [['Rule', 'Requirement', 'Actual', 'Status', 'Suggestion']] + \
            [[r['label'], r['requirement'], r['actual'], r['status'], r['suggestion']] for r in evaluation['results']]
    out['Exercises'] = [ROW_COLUMNS] + raw_rows(workout_infos, rows)
    return out


def to_xlsx(sheet_map):
    from openpyxl import Workbook
    from openpyxl.styles import Font
    wb = Workbook()
    wb.remove(wb.active)
    for name, data in sheet_map.items():
        ws = wb.create_sheet(title=name[:31])
        for row in data:
            ws.append([_cell(v) for v in row])
        for cell in ws[1]:
            cell.font = Font(bold=True)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _cell(v):
    return v if isinstance(v, (int, float, str, bool)) or v is None else str(v)


def to_csv(workout_infos, rows):
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(ROW_COLUMNS)
    writer.writerows(raw_rows(workout_infos, rows))
    return buf.getvalue()


def to_json(analysis, evaluation=None):
    return json.dumps({'analysis': analysis, 'evaluation': evaluation}, indent=2, default=str)
