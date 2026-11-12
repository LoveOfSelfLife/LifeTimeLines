from pathlib import Path

from flask import Flask, render_template

from common.fitness.exercise_history_analytics import GROUP_BY_OPTIONS


SERVICE = Path(__file__).resolve().parents[2] / 'services' / 'fitnessclub'
TEMPLATES = SERVICE / 'templates'


def test_default_and_invalid_grouping_show_individual_exercises(monkeypatch):
    monkeypatch.syspath_prepend(str(SERVICE))
    from views.exercise_history.exercise_history_routes import _view_args

    app = Flask(__name__)
    for query in ('', '?group_by=invalid'):
        with app.test_request_context('/exercise_history/' + query):
            assert _view_args()['group_by'] == 'exercise'
    with app.test_request_context('/exercise_history/?group_by=family'):
        assert _view_args()['group_by'] == 'family'


def test_exercise_history_switches_between_individual_and_grouped_links():
    app = Flask(__name__, template_folder=str(TEMPLATES))
    exercise = {'exercise_id': 'ex-1', 'exercise_name': 'Bench press', 'workout_count': 2,
                'last_date': '2025-01-01', 'volumes': []}
    group = {'group': 'Push', 'exercise_count': 2, 'workout_count': 3,
             'last_date': '2025-01-01', 'volumes': []}
    with app.app_context():
        html = render_template('exercise_history/exercise_history.html', group_by='exercise',
                               group_by_options=GROUP_BY_OPTIONS, groups=[exercise])
        assert 'Group by (optional)' in html
        assert 'No grouping (individual exercises)' in html
        assert 'value="exercise" selected' in html
        assert 'bi-caret-down-fill' in html
        assert 'hx-get="/exercise_history/exercise"' in html
        assert 'ex-1' in html and 'Bench press' in html
        assert 'hx-get="/exercise_history/group"' not in html

        grouped = render_template('exercise_history/_groups.html', group_by='movement', groups=[group])
        assert 'hx-get="/exercise_history/group"' in grouped
        assert 'Push' in grouped and '2 exercises' in grouped

        empty = render_template('exercise_history/_groups.html', group_by='exercise', groups=[])
        assert 'No exercise history yet' in empty
