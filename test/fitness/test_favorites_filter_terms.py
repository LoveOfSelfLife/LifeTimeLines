import unittest
from html.parser import HTMLParser
from pathlib import Path

from flask import Flask, jsonify, render_template, session
from werkzeug.test import Client

from common.filter_funcs import apply_favorites_preference
from common.filter_funcs import get_filter_terms_from_request
from common.filter_funcs import resolve_favorites_filter_terms
from common.filter_funcs import add_filter_terms_summary


class TestResolveFavoritesFilterTerms(unittest.TestCase):

    def test_uses_explicit_requested_state_and_strips_existing_favorites_term(self):
        filter_terms = [
            {"type": "text", "value": "arms"},
            {"type": "favorites", "value": "true"},
        ]

        normalized_terms, favorites_only = resolve_favorites_filter_terms(
            filter_terms,
            requested_favorites_only=False,
            session_favorites_only=True,
        )

        self.assertEqual(normalized_terms, [{"type": "text", "value": "arms"}])
        self.assertFalse(favorites_only)

    def test_uses_existing_favorites_term_when_request_is_not_explicit(self):
        filter_terms = [
            {"type": "text", "value": "arms"},
            {"type": "favorites", "value": "true"},
        ]

        normalized_terms, favorites_only = resolve_favorites_filter_terms(
            filter_terms,
            requested_favorites_only=None,
            session_favorites_only=False,
        )

        self.assertEqual(
            normalized_terms,
            [
                {"type": "text", "value": "arms"},
                {"type": "favorites", "value": "true"},
            ],
        )
        self.assertTrue(favorites_only)


class TestAddFilterTermsSummary(unittest.TestCase):

    def test_ignores_summary_only_terms_without_type(self):
        filter_terms = [
            {"type": "^section", "value": "ramp"},
            {"summary": "^section:ramp"},
            {"type": "favorites", "value": "true"},
        ]

        summary = add_filter_terms_summary(filter_terms)

        self.assertEqual(summary, [{"summary": "^section:ramp"}])

    def test_falls_back_to_session_state_when_nothing_is_explicit(self):
        filter_terms = [{"type": "text", "value": "arms"}]

        normalized_terms, favorites_only = resolve_favorites_filter_terms(
            filter_terms,
            requested_favorites_only=None,
            session_favorites_only=True,
        )

        self.assertEqual(
            normalized_terms,
            [
                {"type": "text", "value": "arms"},
                {"type": "favorites", "value": "true"},
            ],
        )
        self.assertTrue(favorites_only)


class TestFavoritesPreferencesByEntity(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        app.secret_key = 'test-secret'

        @app.route('/listing/<entity_name>', methods=['GET', 'POST'])
        def listing(entity_name):
            return jsonify(get_filter_terms_from_request(entity_name))

        @app.route('/legacy-session', methods=['POST'])
        def legacy_session():
            session['favorites_preference'] = True
            return '', 204

        @app.route('/return/<entity_name>', methods=['POST'])
        def return_to_listing(entity_name):
            return jsonify(apply_favorites_preference([], entity_name))

        self.client = Client(app, app.response_class)

    def test_preferences_are_independent_and_persist_across_requests(self):
        exercises = '/listing/ExerciseTable'
        programs = '/listing/MemberProgramsTable'

        self.client.post('/legacy-session')
        self.assertEqual(self.client.get(programs).json, [])
        self.client.post(exercises, data={'favorites_only': 'true'})
        self.assertEqual(self.client.get(programs).json, [])
        self.assertEqual(self.client.get(exercises).json, [
            {'type': 'favorites', 'value': 'true', 'entity_table': 'ExerciseTable'},
        ])

        self.client.post(programs, data={'favorites_only': 'true'})
        self.client.post(exercises, data={'favorites_only': 'false'})
        self.assertEqual(self.client.get(exercises).json, [])
        self.assertEqual(self.client.get(programs).json, [
            {'type': 'favorites', 'value': 'true', 'entity_table': 'MemberProgramsTable'},
        ])

    def test_foreign_or_legacy_filter_terms_do_not_override_preference(self):
        self.client.post('/listing/ExerciseTable', data={'favorites_only': 'true'})
        exercise_terms = self.client.get('/listing/ExerciseTable').json
        response = self.client.get(
            '/listing/MemberProgramsTable',
            query_string={'filter': repr(exercise_terms)},
        )
        self.assertEqual(response.json, [])
        legacy = [{'type': 'favorites', 'value': 'true'}]
        self.assertEqual(self.client.get(
            '/listing/MemberProgramsTable', query_string={'filter': repr(legacy)},
        ).json, [])

    def test_scoped_form_value_and_matching_filter_term(self):
        endpoint = '/listing/ExerciseTable'
        response = self.client.post(endpoint, data={
            'favorites_only_ExerciseTable': 'true',
            'favorites_only_MemberProgramsTable': 'false',
            'search': 'arms',
        })
        self.assertEqual(response.json[0], {'type': 'text', 'value': 'arms'})
        favorites = response.json[-1]
        self.assertEqual(favorites['entity_table'], 'ExerciseTable')
        self.assertEqual(self.client.get(endpoint, query_string={'filter': repr([favorites])}).json, [favorites])
        self.assertEqual(self.client.post(endpoint, data={
            'favorites_only_ExerciseTable': 'true', 'favorites_only': 'false',
        }).json, [])

    def test_scoped_query_state_and_search_preserve_preference(self):
        endpoint = '/listing/ExerciseTable'
        self.client.post(endpoint, data={'favorites_only': 'true'})
        terms = self.client.get(endpoint, query_string={
            'favorites_only_ExerciseTable': 'true',
            'favorites_only_MemberProgramsTable': 'false',
            'search': 'squat',
            'page': 2,
            'view': 'card',
        }).json
        self.assertIn({'type': 'text', 'value': 'squat'}, terms)
        self.assertIn({'type': 'favorites', 'value': 'true', 'entity_table': 'ExerciseTable'}, terms)
        self.assertEqual(self.client.get('/listing/MemberProgramsTable').json, [])

    def test_preferences_are_isolated_between_sessions(self):
        other_client = Client(self.client.application, self.client.application.response_class)
        self.client.post('/listing/ExerciseTable', data={'favorites_only': 'true'})
        self.assertEqual(other_client.get('/listing/ExerciseTable').json, [])

    def test_return_to_listing_restores_session_preference(self):
        self.client.post('/listing/ExerciseTable', data={'favorites_only': 'true'})
        self.assertEqual(self.client.post('/return/ExerciseTable').json, [
            {'type': 'favorites', 'value': 'true', 'entity_table': 'ExerciseTable'},
        ])

    def test_scoped_favorites_filter_selects_only_favorites(self):
        from common.entities_getter import generic_entity_filter

        class Entity(dict):
            key_field = 'id'

        terms = self.client.post(
            '/listing/ExerciseTable', data={'favorites_only': 'true'},
        ).json
        entities = [Entity(id='favorite'), Entity(id='other')]
        self.assertEqual(
            generic_entity_filter(entities, terms, favorite_entity_ids={'favorite'}),
            [entities[0]],
        )
        program_terms = self.client.get('/listing/MemberProgramsTable').json
        self.assertEqual(
            generic_entity_filter(entities, program_terms, favorite_entity_ids={'favorite'}),
            entities,
        )


class ElementParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.elements = []

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))


class TestFavoritesListRendering(unittest.TestCase):
    def test_full_and_partial_templates_scope_state_and_oob_updates(self):
        root = Path(__file__).resolve().parents[2]
        app = Flask(__name__, template_folder=str(root / 'common' / 'templates'))
        for entity_table in ('ExerciseTable', 'MemberProgramsTable'):
            for active in (True, False):
                terms = ([{'type': 'favorites', 'value': 'true', 'entity_table': entity_table}]
                         if active else [])
                for template in ('entity_list_component.html', 'entity_results_partial.html'):
                    with app.test_request_context():
                        html = render_template(
                            template, entity_name=entity_table, filter_terms=terms,
                            main_content_container='entities-container',
                            entities_listing_route='/listing?', entities=[], fields_to_display={'listing_view': []},
                            view='list', page=1, total_pages=2,
                        )
                    parser = ElementParser()
                    parser.feed(html)
                    buttons = [attrs for tag, attrs in parser.elements
                               if tag == 'button' and attrs.get('id') == f'favorites-toggle-{entity_table}']
                    states = [attrs for tag, attrs in parser.elements
                              if tag == 'input' and attrs.get('id') == f'favorites-only-state-{entity_table}']
                    self.assertTrue(buttons)
                    self.assertTrue(states)
                    for button in buttons:
                        self.assertEqual(button['data-favorites'], str(active).lower())
                        self.assertIn(f'"favorites_only": {str(not active).lower()}', button['hx-vals'])
                    for state in states:
                        self.assertEqual(state['name'], f'favorites_only_{entity_table}')
                        self.assertEqual(state['value'], str(active).lower())
                    includes = [attrs['hx-include'] for _, attrs in parser.elements
                                if 'favorites_only_' in attrs.get('hx-include', '')]
                    self.assertTrue(includes)
                    for include in includes:
                        self.assertIn(f"favorites_only_{entity_table}", include)
                    if template == 'entity_results_partial.html':
                        self.assertEqual(buttons[0]['hx-swap-oob'], 'true')
                        self.assertEqual(states[0]['hx-swap-oob'], 'true')

    def test_item_heart_receives_current_filter_state(self):
        root = Path(__file__).resolve().parents[2]
        app = Flask(__name__, template_folder=str(root / 'common' / 'templates'))
        for view in ('list', 'card'):
            for active in (True, False):
                with app.test_request_context():
                    html = render_template(
                        'entity_results_partial.html',
                        entity_name='ExerciseTable',
                        filter_terms=[{'type': 'favorites', 'value': 'true'}] if active else [],
                        entities=[{'entity_id': 'one', 'key': 'one', 'field_values': ['One'],
                                   'is_favorite': True,
                                   'card_view_fields': {'title': 'One', 'subtitle': '', 'description': ''}}],
                        fields_to_display={'listing_view': ['Name']},
                        main_content_container='entities-container',
                        entities_listing_route='/listing?', view=view, page=1, total_pages=1,
                    )
                parser = ElementParser()
                parser.feed(html)
                item_button = next(attrs for tag, attrs in parser.elements
                                   if tag == 'button' and attrs.get('aria-label') == 'Unfavorite')
                self.assertIn(f'"favorites_only": {str(active).lower()}', item_button['hx-vals'])


if __name__ == "__main__":
    unittest.main()
