"""Presentation helpers for the Exercise History page: plotly charts and display rows over the analytics queries."""
import plotly.graph_objects as go
import plotly.io as pio

from common.fitness.exercise_analytics_queries import GROUP_BY_OPTIONS  # noqa: F401  (re-exported for the routes)

# perhaps this should be configurable or moved to a settings file ???? TBD
ANALYTICS_DB_PATH = '/share/FitnessClub/workouts.sqlite'

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

VOLUME_KIND_LABELS = {
    'load': 'kg x reps',
    'reps': 'bodyweight reps',
    'time': 'seconds',
}


def label_volumes(items):
    """adds a display label to the volume kinds of group/exercise summary rows"""
    for item in items:
        for v in item['volumes']:
            v['label'] = VOLUME_KIND_LABELS.get(v['kind'], v['kind'])
    return items


def build_chart_json(series_rows, metric='volume', title=None):
    """plotly figure as a JSON string that is safe to embed in a <script> block, or None when there is nothing to plot"""
    if not series_rows:
        return None
    by_series = {}
    for r in series_rows:
        by_series.setdefault(r['series'], []).append(r)
    fig = go.Figure()
    for name, rows in by_series.items():
        fig.add_trace(go.Scatter(x=[r['period'] for r in rows], y=[r['value'] for r in rows], name=name,
                                 mode='lines+markers'))
    fig.update_layout(
        title=title,
        template='plotly_white',
        margin=dict(l=50, r=20, t=50 if title else 20, b=40),
        legend=dict(orientation='h', y=-0.2),
        yaxis_title=METRIC_OPTIONS.get(metric, metric),
        height=380,
    )
    return pio.to_json(fig).replace('</', '<\\/')


def _fmt(value):
    if value is None:
        return ''
    return f"{value:.1f}".rstrip('0').rstrip('.')


def workout_rows(history_rows):
    """display rows for the per-workout table of an exercise (rows from exercise_analytics_queries.exercise_history)"""
    def volume(r):
        if r['volume_kind'] == 'load':
            return r['volume_kg']
        if r['volume_kind'] == 'reps':
            return r['total_reps']
        if r['volume_kind'] == 'time':
            return r['total_time_sec']
        return None

    return [{
        'date': r['performed_ts'][:10],
        'sets': _fmt(r['sets']),
        'reps': _fmt(r['reps']),
        'weight': _fmt(r['weight_kg']),
        'time': _fmt(r['time_sec']),
        'volume': _fmt(volume(r)),
        'volume_label': VOLUME_KIND_LABELS.get(r['volume_kind'], ''),
    } for r in history_rows]
