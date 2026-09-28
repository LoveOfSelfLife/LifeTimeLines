import unittest

from common.fitness.hx_common import add_filter_terms_summary, resolve_favorites_filter_terms


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


if __name__ == "__main__":
    unittest.main()
