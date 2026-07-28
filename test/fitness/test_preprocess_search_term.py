import unittest

from common.fitness.hx_common import preprocess_search_term


class TestPreprocessSearchTerm(unittest.TestCase):

    def test_plain_text_returns_single_text_filter(self):
        result = preprocess_search_term("arms and equip:barbell")
        self.assertEqual(
            result,
            [{"type": "text", "value": "arms and equip:barbell"}],
        )

    def test_section_prefix_only(self):
        result = preprocess_search_term("^section:arms")
        self.assertEqual(
            result,
            [{"type": "^section", "value": "arms"}],
        )

    def test_related_prefix_only(self):
        result = preprocess_search_term("^related:12345")
        self.assertEqual(
            result,
            [{"type": "^related", "value": "12345"}],
        )

    def test_section_prefix_with_remainder_text(self):
        result = preprocess_search_term("^section:arms and equip:barbell")
        self.assertEqual(
            result,
            [
                {"type": "^section", "value": "arms"},
                {"type": "text", "value": "and equip:barbell"},
            ],
        )

    def test_related_prefix_with_remainder_text(self):
        result = preprocess_search_term("^related:12345 and equip:barbell")
        self.assertEqual(
            result,
            [
                {"type": "^related", "value": "12345"},
                {"type": "text", "value": "and equip:barbell"},
            ],
        )

    def test_chained_prefixes_no_text_tail(self):
        result = preprocess_search_term("^section:core ^related:12345")
        self.assertEqual(
            result,
            [
                {"type": "^section", "value": "core"},
                {"type": "^related", "value": "12345"},
            ],
        )

    def test_chained_prefixes_with_text_tail(self):
        result = preprocess_search_term("^section:core ^related:12345 and equip:barbell")
        self.assertEqual(
            result,
            [
                {"type": "^section", "value": "core"},
                {"type": "^related", "value": "12345"},
                {"type": "text", "value": "and equip:barbell"},
            ],
        )

    def test_leading_whitespace_is_ignored(self):
        result = preprocess_search_term("   ^section:legs")
        self.assertEqual(
            result,
            [{"type": "^section", "value": "legs"}],
        )

    def test_text_with_leading_whitespace_is_trimmed(self):
        result = preprocess_search_term("   free text")
        self.assertEqual(
            result,
            [{"type": "text", "value": "free text"}],
        )


if __name__ == "__main__":
    unittest.main()
