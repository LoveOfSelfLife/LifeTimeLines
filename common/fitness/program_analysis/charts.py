"""Plotly figures (as JSON strings that are safe to embed in a <script> block) for the program analysis report."""
import plotly.graph_objects as go
import plotly.io as pio

STATUS_COLORS = {'met': '#2e9e5b', 'under': '#e0a100', 'over': '#d64545'}
BUCKET_COLORS = {'strength': '#2f6fdb', 'mobility': '#2e9e5b', 'flexibility': '#8a5fd1', 'myofascia': '#e08a1e',
                 'other': '#7f8c8d', 'unspecified': '#bbbbbb'}


def _json(fig, height=None):
    fig.update_layout(template='plotly_white', margin=dict(l=10, r=10, t=40, b=10),
                      legend=dict(orientation='h', yanchor='bottom', y=-0.35), **({'height': height} if height else {}))
    return pio.to_json(fig).replace('</', '<\\/')


def _workout_names(analysis):
    return [f"{w['idx'] + 1}. {w['name']}" for w in analysis['workouts']]


def _stacked_by_workout(analysis, table, title, field, ytitle):
    names = _workout_names(analysis)
    fig = go.Figure()
    for key, cell in sorted(table.items()):
        if cell['total_exercises'] > 0:
            fig.add_bar(name=key, x=names, y=cell[field])
    fig.update_layout(barmode='stack', title=title, yaxis_title=ytitle)
    return _json(fig, 380)


def _heatmap(analysis, table, keys, title):
    names = _workout_names(analysis)
    z = [table[k]['sets'] if k in table else [0] * len(names) for k in keys]
    fig = go.Figure(go.Heatmap(z=z, x=names, y=keys, colorscale='Blues', zmin=0,
                               hovertemplate='%{y} in %{x}: %{z:g} sets<extra></extra>'))
    fig.update_layout(title=title, yaxis=dict(autorange='reversed'))
    return _json(fig, max(260, 26 * len(keys) + 100))


def _muscle_bars(analysis):
    fig = go.Figure()
    for bucket, table in analysis['tables']['muscle'].items():
        cells = {m: c for m, c in table.items() if c['total_sets'] > 0}
        if cells:
            ordered = sorted(cells, key=lambda m: cells[m]['total_sets'])
            fig.add_bar(name=bucket, y=ordered, x=[cells[m]['total_sets'] for m in ordered], orientation='h',
                        marker_color=BUCKET_COLORS[bucket])
    fig.update_layout(barmode='stack', title='Muscles worked, by purpose (weighted sets)', xaxis_title='sets')
    return _json(fig, max(360, 28 * len(analysis['expected']['muscle']) + 120))


def _pfc_donut(analysis):
    pfc = {k: c['total_sets'] for k, c in analysis['tables']['pfc'].items() if c['total_sets'] > 0}
    fig = go.Figure(go.Pie(labels=list(pfc), values=list(pfc.values()), hole=0.5, sort=False))
    fig.update_layout(title='Fitness components (sets)')
    return _json(fig, 360)


def _objective_chart(evaluation):
    results = evaluation['results']
    labels = [f"{r['label']} ({r['purpose'] + ', ' if r['purpose'] else ''}{r['metric'].replace('_', ' ')})" for r in results]
    fig = go.Figure(go.Bar(
        y=labels, x=[r['actual'] for r in results], orientation='h',
        marker_color=[STATUS_COLORS[r['status']] for r in results],
        text=[r['requirement'] for r in results], textposition='outside', cliponaxis=False,
        hovertemplate='%{y}: %{x:g}<extra></extra>'))
    fig.update_layout(title=f"Objective: {evaluation['objective']} — {evaluation['met']} of {evaluation['total']} met",
                      yaxis=dict(autorange='reversed'), margin=dict(r=140))
    return _json(fig, max(300, 26 * len(results) + 120))


def build_charts(analysis, evaluation=None):
    """chart id -> figure JSON; charts with nothing to plot are left out"""
    t = analysis['tables']
    charts = {}
    if not analysis['totals']['exercises']:
        return charts
    charts['patterns'] = _stacked_by_workout(analysis, t['pattern'], 'Movement patterns by workout (sets)', 'sets', 'sets')
    charts['parents'] = _stacked_by_workout(analysis, t['parent_pattern'], 'Movement families by workout (sets)', 'sets', 'sets')
    charts['pattern_heatmap'] = _heatmap(analysis, t['pattern'], analysis['expected']['pattern'],
                                         'Movement patterns × workouts (sets)')
    charts['muscle_heatmap'] = _heatmap(analysis, t['muscle']['strength'], analysis['expected']['muscle'],
                                        'Strengthened muscles × workouts (weighted sets)')
    charts['muscles'] = _muscle_bars(analysis)
    charts['pfc'] = _pfc_donut(analysis)
    charts['laterality'] = _stacked_by_workout(analysis, t['laterality'], 'Bilateral vs unilateral by workout (exercises)',
                                               'exercises', 'exercises')
    if evaluation and evaluation['results']:
        charts['objective'] = _objective_chart(evaluation)
    return charts
