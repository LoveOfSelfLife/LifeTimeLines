"""
Analytics over a member's exercise event history: grouping exercises (by family, movement category, muscle,
equipment, or not at all), computing volume metrics with pandas, and building plotly figures.
"""
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

from common.entity_store import EntityStore
from common.fitness.exercise_entity import ExerciseEntity
from common.fitness.member_exercise_history import list_exercise_events_for_member, sync_exercise_history_for_member

LBS_TO_KG = 0.45359237

GROUP_BY_OPTIONS = {
    'family': 'Exercise family',
    'movement': 'Movement pattern',
    'muscle': 'Primary muscle',
    'equipment': 'Equipment',
    'exercise': 'Individual exercise',
}

METRIC_OPTIONS = {
    'volume': 'Volume',
    'reps': 'Total reps',
    'sets': 'Total sets',
    'max_weight': 'Max weight (kg)',
}

RESOLUTION_OPTIONS = {
    'workout': 'Per workout',
    'week': 'Weekly',
    'month': 'Monthly',
}

# the natural volume metric of an exercise event depends on what was recorded for it
VOLUME_KINDS = {
    'load': 'kg x reps',
    'reps': 'bodyweight reps',
    'time': 'seconds',
}

NO_GROUP = '(none)'

EVENT_COLUMNS = ['date', 'workout_id', 'exercise_id', 'exercise_name', 'group_family', 'group_movement',
                 'group_muscle', 'group_equipment', 'sets', 'reps', 'weight_kg', 'time_sec', 'volume_kind',
                 'volume', 'total_reps']


def _num(value):
    """parameter values may be numbers, numeric strings, or non-numeric (e.g. a band colour); returns a float or None"""
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _weight_in_kg(weight, unit):
    w = _num(weight)
    if w is None:
        return None
    unit = (unit or 'kg').strip().lower()
    if unit in ('kg', 'kgs', 'kilograms'):
        return w
    if unit in ('lb', 'lbs', 'pounds'):
        return w * LBS_TO_KG
    return None


def _as_list(value):
    if not value:
        return []
    if isinstance(value, (list, tuple)):
        return [str(v) for v in value if v]
    return [str(value)]


def compute_event_metrics(event):
    """
    turns one raw exercise event into its computed metrics.
    volume is the exercise's natural measure:  load (sets x reps x kg), bodyweight reps (sets x reps),
    or time (sets x seconds).
    """
    sets = _num(event.get('sets'))
    reps = _num(event.get('reps'))
    time_sec = _num(event.get('time'))
    weight_kg = _weight_in_kg(event.get('weight'), event.get('weight_unit'))
    if sets is None:
        sets = 1.0

    total_reps = sets * reps if reps else 0.0
    if reps and weight_kg:
        kind, volume = 'load', total_reps * weight_kg
    elif reps:
        kind, volume = 'reps', total_reps
    elif time_sec:
        kind, volume = 'time', sets * time_sec
    else:
        kind, volume = None, 0.0
    return {'sets': sets, 'reps': reps, 'weight_kg': weight_kg, 'time_sec': time_sec,
            'volume_kind': kind, 'volume': volume, 'total_reps': total_reps}


def build_history_dataframe(events, exercises_by_id):
    """
    events: iterable of MemberExerciseEventHistoryEntity-like dicts
    exercises_by_id: dict of exercise id -> ExerciseEntity (or None if the exercise no longer exists)
    returns a DataFrame with one row per event, where the group_* columns hold the list of groups
    that the event's exercise belongs to for each grouping dimension.
    """
    rows = []
    for event in events:
        exercise_id = event.get('exercise_id')
        exercise = exercises_by_id.get(exercise_id) or {}
        name = exercise.get('name') or exercise_id
        family = (exercise.get('family') or '').strip() or name
        row = {
            'date': event.get('date_time'),
            'workout_id': event.get('member_workout_instance_id') or event.get('event_id'),
            'exercise_id': exercise_id,
            'exercise_name': name,
            'group_family': [family],
            'group_movement': _as_list(exercise.get('movement_categories')) or [NO_GROUP],
            'group_muscle': _as_list(exercise.get('primaryMuscles')) or [NO_GROUP],
            'group_equipment': _as_list(exercise.get('equipment_list')) or [NO_GROUP],
        }
        row.update(compute_event_metrics(event))
        rows.append(row)

    df = pd.DataFrame(rows, columns=EVENT_COLUMNS)
    if df.empty:
        return df
    df['date'] = pd.to_datetime(df['date'], utc=True, errors='coerce').dt.tz_localize(None)
    return df.dropna(subset=['date']).sort_values('date').reset_index(drop=True)


def load_member_history(member_id, sync=False):
    """loads the member's exercise events into a DataFrame; with sync=True the event history is first topped up from workout instances"""
    events =  sync_exercise_history_for_member(member_id) if sync else list_exercise_events_for_member(member_id)
    es = EntityStore()
    exercises_by_id = {}
    for exercise_id in {e.get('exercise_id') for e in events}:
        exercises_by_id[exercise_id] = es.get_item(ExerciseEntity({'id': exercise_id}))
    return build_history_dataframe(events, exercises_by_id)


def _group_column(group_by):
    return {'family': 'group_family', 'movement': 'group_movement',
            'muscle': 'group_muscle', 'equipment': 'group_equipment'}.get(group_by)


def with_group(df, group_by):
    """
    adds a 'group' column.  Dimensions where an exercise can belong to several groups (movement pattern, muscle,
    equipment) repeat the event once per group, so the event counts fully in every group it belongs to.
    """
    out = df.copy()
    column = _group_column(group_by)
    if column is None:
        out['group'] = out['exercise_name']
    else:
        out['group'] = out[column]
        out = out.explode('group')
    return out


def summarize_groups(df, group_by):
    """one row per group: number of exercises & workouts, last date, and total volume of each volume kind"""
    if df.empty:
        return []
    g = with_group(df, group_by)
    summaries = []
    for group, gdf in g.groupby('group'):
        summaries.append({
            'group': group,
            'exercise_count': gdf['exercise_id'].nunique(),
            'workout_count': gdf['workout_id'].nunique(),
            'last_date': gdf['date'].max().strftime('%Y-%m-%d'),
            'volumes': _volumes_by_kind(gdf),
        })
    summaries.sort(key=lambda s: (s['group'] == NO_GROUP, -s['workout_count'], s['group']))
    return summaries


def _volumes_by_kind(df):
    totals = df.groupby('volume_kind')['volume'].sum()
    return [{'kind': k, 'label': VOLUME_KINDS[k], 'value': round(float(totals[k]), 1)}
            for k in VOLUME_KINDS if k in totals.index and totals[k] > 0]


def summarize_exercises(df):
    """one row per exercise in df"""
    rows = []
    for exercise_id, edf in df.groupby('exercise_id'):
        rows.append({
            'exercise_id': exercise_id,
            'exercise_name': edf['exercise_name'].iloc[0],
            'workout_count': edf['workout_id'].nunique(),
            'last_date': edf['date'].max().strftime('%Y-%m-%d'),
            'volumes': _volumes_by_kind(edf),
        })
    rows.sort(key=lambda r: (-r['workout_count'], r['exercise_name']))
    return rows


def group_events(df, group_by, group):
    g = with_group(df, group_by)
    return g[g['group'] == group]


def exercise_events(df, exercise_id):
    return df[df['exercise_id'] == exercise_id]


def workout_rows(df):
    """the individual workout entries of an exercise, most recent first, ready for display"""
    rows = []
    for r in df.sort_values('date', ascending=False).itertuples():
        rows.append({
            'date': r.date.strftime('%Y-%m-%d'),
            'sets': _fmt(r.sets),
            'reps': _fmt(r.reps),
            'weight': _fmt(r.weight_kg),
            'time': _fmt(r.time_sec),
            'volume': _fmt(r.volume),
            'volume_label': VOLUME_KINDS.get(r.volume_kind, ''),
        })
    return rows


def _fmt(value):
    if value is None or pd.isna(value):
        return ''
    return f"{value:.1f}".rstrip('0').rstrip('.')


def aggregate_over_time(df, metric, resolution):
    """
    returns a DataFrame of (period, series, value) where period is the workout date, or the start of the
    week or month.  'volume' yields one series per volume kind, since kg x reps, reps and seconds can't be summed.
    """
    if df.empty:
        return pd.DataFrame(columns=['period', 'series', 'value'])

    work = df.copy()
    if resolution == 'week':
        work['period'] = work['date'].dt.to_period('W').dt.start_time
    elif resolution == 'month':
        work['period'] = work['date'].dt.to_period('M').dt.start_time
    else:
        # one point per workout, placed at the workout's own date & time
        work['period'] = work.groupby('workout_id')['date'].transform('min')

    if metric == 'reps':
        work['series'], work['value'] = 'Total reps', work['total_reps']
        how = 'sum'
    elif metric == 'sets':
        work['series'], work['value'] = 'Total sets', work['sets']
        how = 'sum'
    elif metric == 'max_weight':
        work = work.dropna(subset=['weight_kg'])
        work['series'], work['value'] = 'Max weight (kg)', work['weight_kg']
        how = 'max'
    else:
        work = work[work['volume_kind'].notna()]
        work['series'] = work['volume_kind'].map(lambda k: f"Volume ({VOLUME_KINDS[k]})")
        work['value'] = work['volume']
        how = 'sum'

    if work.empty:
        return pd.DataFrame(columns=['period', 'series', 'value'])
    return work.groupby(['period', 'series'], as_index=False)['value'].agg(how).sort_values('period')


def build_chart_json(df, metric='volume', resolution='workout', title=None):
    """plotly figure as a JSON string that is safe to embed in a <script> block, or None when there is nothing to plot"""
    data = aggregate_over_time(df, metric, resolution)
    if data.empty:
        return None
    fig = go.Figure()
    for series, sdf in data.groupby('series'):
        fig.add_trace(go.Scatter(x=sdf['period'], y=sdf['value'], name=series,
                                 mode='lines+markers', line_shape='linear'))
    fig.update_layout(
        title=title,
        template='plotly_white',
        margin=dict(l=50, r=20, t=50 if title else 20, b=40),
        legend=dict(orientation='h', y=-0.2),
        xaxis_title=None,
        yaxis_title=METRIC_OPTIONS.get(metric, metric),
        height=380,
    )
    return pio.to_json(fig).replace('</', '<\\/')
