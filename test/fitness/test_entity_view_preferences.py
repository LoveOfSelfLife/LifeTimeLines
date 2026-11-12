import unittest
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch

from flask import Flask, jsonify, render_template, session
from werkzeug.test import Client

from common.filter_funcs import get_entity_view_from_request


class TestEntityViewPreferences(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        app.secret_key = 'test-secret'

        @app.route('/listing/<entity_table>', methods=['GET', 'POST'])
        def listing(entity_table):
            return jsonify(view=get_entity_view_from_request(entity_table))

        @app.route('/legacy', methods=['POST'])
        def legacy():
            session['view_preference'] = 'card'
            return '', 204

        @app.route('/modified/<entity_table>', methods=['POST'])
        def modified(entity_table):
            get_entity_view_from_request(entity_table)
            return jsonify(modified=session.modified)

        @app.route('/cached/<entity_table>/<member_id>', methods=['GET', 'POST'])
        def cached(entity_table, member_id):
            view = get_entity_view_from_request(
                entity_table, member_id=member_id, legacy_cache_key=f'view_preference_{member_id}',
            )
            return jsonify(view=view, modified=session.modified)

        self.client = Client(app, app.response_class)

    def test_view_state_is_independent_and_persistent(self):
        exercise = '/listing/ExerciseTable'
        workout = '/listing/MemberWorkoutDefinitionTable'
        self.client.post('/legacy')
        self.assertEqual(self.client.get(workout).json['view'], 'list')
        self.assertEqual(self.client.get(exercise, query_string={'view': 'card'}).json['view'], 'card')
        self.assertEqual(self.client.get(workout).json['view'], 'list')
        self.assertEqual(self.client.get(exercise).json['view'], 'card')
        self.client.get(workout, query_string={'view': 'card'})
        self.client.get(exercise, query_string={'view': 'list'})
        self.assertEqual(self.client.get(workout).json['view'], 'card')

    def test_scoped_post_and_explicit_toggle_precedence(self):
        path = '/listing/ExerciseTable'
        self.client.get(path, query_string={'view': 'card'})
        self.assertEqual(self.client.post(path, data={
            'view_ExerciseTable': 'card',
            'view_MemberWorkoutDefinitionTable': 'list',
            'favorites_only': 'true',
        }).json['view'], 'card')
        self.assertEqual(self.client.get(path, query_string={
            'view': 'list', 'view_ExerciseTable': 'card',
        }).json['view'], 'list')
        self.assertEqual(self.client.get('/listing/MemberWorkoutDefinitionTable').json['view'], 'list')

    def test_invalid_view_is_rejected_without_changing_preference(self):
        path = '/listing/ExerciseTable'
        self.client.get(path, query_string={'view': 'card'})
        self.assertEqual(self.client.get(path, query_string={'view': 'bad'}).status_code, 400)
        self.assertEqual(self.client.get(path).json['view'], 'card')

    def test_session_isolation(self):
        other_client = Client(self.client.application, self.client.application.response_class)
        self.client.get('/listing/ExerciseTable', query_string={'view': 'card'})
        self.assertEqual(other_client.get('/listing/ExerciseTable').json['view'], 'list')

    def test_default_view_does_not_write_the_session(self):
        response = self.client.post('/modified/ExerciseTable', data={'view_ExerciseTable': 'list'})
        self.assertFalse(response.json['modified'])

    def test_member_cache_is_table_scoped_and_preserves_legacy_exercise_view(self):
        cache = {'view_preference_member1': 'card'}
        with patch('common.filter_funcs.get_cache_value', side_effect=cache.get), \
             patch('common.filter_funcs.set_cache_value', side_effect=cache.__setitem__):
            exercise = '/cached/ExerciseTable/member1'
            workout = '/cached/MemberWorkoutDefinitionTable/member2'
            response = self.client.get(exercise)
            self.assertEqual(response.json, {'view': 'card', 'modified': False})
            self.assertEqual(self.client.get(workout).json['view'], 'list')
            self.assertEqual(self.client.get(exercise, query_string={'view': 'list'}).json,
                             {'view': 'list', 'modified': False})
            self.assertEqual(cache['entity_view_preference_ExerciseTable_member1'], 'list')
            self.assertEqual(self.client.get(exercise).json['view'], 'list')
            self.assertEqual(self.client.get('/cached/ExerciseTable/member2').json['view'], 'list')


class ElementParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.elements = []

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))


class TestEntityViewTemplate(unittest.TestCase):
    def test_view_controls_and_hidden_fields_are_scoped(self):
        root = Path(__file__).resolve().parents[2]
        app = Flask(__name__, template_folder=str(root / 'common' / 'templates'))
        for entity in ('ExerciseTable', 'MemberWorkoutDefinitionTable'):
            for view in ('card', 'list'):
                with app.test_request_context():
                    html = render_template(
                        'entity_list_component.html', entity_name=entity, view=view,
                        main_content_container='entities-container', entities_listing_route='/listing?',
                        entities=[], fields_to_display={'listing_view': []}, filter_terms=[],
                        page=1, total_pages=2, args={'view': 'list'},
                    )
                parser = ElementParser()
                parser.feed(html)
                state = next(attrs for tag, attrs in parser.elements
                             if tag == 'input' and attrs.get('name') == f'view_{entity}')
                self.assertEqual(state['value'], view)
                buttons = [attrs for tag, attrs in parser.elements
                           if tag == 'button' and attrs.get('data-view')]
                for button in buttons:
                    self.assertEqual('active' in button['class'].split(), button['data-view'] == view)
                    self.assertIn(f'"view": "{button["data-view"]}"', button['hx-vals'])
                page_links = [attrs for tag, attrs in parser.elements
                              if tag == 'a' and attrs.get('class') == 'page-link']
                self.assertTrue(page_links)
                for link in page_links:
                    self.assertIn(f'"view": "{view}"', link['hx-vals'])
                includes = [attrs['hx-include'] for _, attrs in parser.elements
                            if f'view_{entity}' in attrs.get('hx-include', '')]
                self.assertTrue(includes)


class TestListingRouteViewIntegration(unittest.TestCase):
    def test_exercise_workout_and_program_listings_share_scoped_preferences(self):
        from services.fitnessclub.views.exercises import exercise_routes
        from services.fitnessclub.views.workouts import workout_routes
        from services.fitnessclub.views.program import programs_routes

        app = Flask(__name__)
        app.secret_key = 'test-secret'

        @app.route('/exercises', methods=['GET', 'POST'])
        def exercises():
            return jsonify(view=exercise_routes.exercises_listing2({}, 'member'))

        @app.route('/workouts', methods=['GET', 'POST'])
        def workouts():
            return jsonify(view=workout_routes.workouts_listing2({}))

        @app.route('/builder-exercises', methods=['GET', 'POST'])
        def builder_exercises():
            return jsonify(view=workout_routes.exercise_listing.__wrapped__(context={}))

        @app.route('/programs', methods=['GET', 'POST'])
        def programs():
            return jsonify(view=programs_routes.programs_listing2({}))

        def selected_view(*args, **kwargs):
            return args[4]

        cache = {}
        with patch('common.filter_funcs.get_cache_value', side_effect=cache.get), \
             patch('common.filter_funcs.set_cache_value', side_effect=cache.__setitem__), \
             patch.object(exercise_routes, 'get_fitnessclub_listing_fields_for_entity'), \
             patch.object(exercise_routes, 'get_entities', return_value=[]), \
             patch.object(exercise_routes, 'resolve_selected_entity_keys', return_value=[]), \
             patch.object(exercise_routes, 'exercise_listing_base', side_effect=selected_view), \
             patch.object(workout_routes, 'get_member_id_from_user_context', return_value='member'), \
             patch.object(workout_routes, 'get_fitnessclub_listing_fields_for_entity'), \
             patch.object(workout_routes, 'get_entities', return_value=[]), \
             patch.object(workout_routes, 'get_entity_obj_from_entity_name'), \
             patch.object(workout_routes, 'hx_render_template', side_effect=lambda template, **kwargs: kwargs['view']), \
             patch.object(workout_routes, 'resolve_selected_workout_keys', return_value=[]), \
             patch.object(workout_routes, 'filter_entities_by_member_role', side_effect=lambda member, entities: entities), \
             patch.object(workout_routes, 'workouts_listing_base', side_effect=selected_view), \
             patch.object(programs_routes, 'get_member_id_from_user_context', return_value='member'), \
             patch.object(programs_routes, 'get_fitnessclub_listing_fields_for_entity'), \
             patch.object(programs_routes, 'get_entities', return_value=[]), \
             patch.object(programs_routes, 'filter_entities_by_member_role', side_effect=lambda member, entities: entities), \
             patch.object(programs_routes, 'program_listing_base', side_effect=selected_view):
            client = Client(app, app.response_class)
            self.assertEqual(client.get('/exercises?view=card').json['view'], 'card')
            self.assertEqual(client.get('/workouts').json['view'], 'list')
            self.assertEqual(client.get('/programs').json['view'], 'list')
            self.assertEqual(client.get('/builder-exercises').json['view'], 'card')
            self.assertEqual(client.post('/exercises', data={
                'view_ExerciseTable': 'card',
            }).json['view'], 'card')
            self.assertEqual(client.get('/exercises').json['view'], 'card')


if __name__ == '__main__':
    unittest.main()
