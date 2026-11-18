import unittest

from werkzeug.datastructures import MultiDict

from common.facets import (FacetDef, apply_selection, compute_facet_counts,
                           parse_selection, selected_chips)
from common.fitness.exercise_entity import exercise_facets

EXERCISES = [
    {"name": "bench", "primaryMuscles": ["chest"], "secondaryMuscles": ["triceps"],
     "equipment_list": ["barbell"], "origin": "wger", "is_unilateral": False},
    {"name": "fly", "primaryMuscles": ["chest"], "equipment_list": ["dumbbell"],
     "origin": "custom", "is_unilateral": False, "setCompletionMeasure": "time"},
    {"name": "curl", "primaryMuscles": ["biceps"], "equipment_list": ["dumbbell"],
     "origin": "wger", "is_unilateral": True},
    {"name": "plank", "primaryMuscles": ["abdominals"]},
]
FACETS = {f.key: f for f in exercise_facets}
DEFS = list(exercise_facets)


def names(items):
    return [i["name"] for i in items]


class TestFacets(unittest.TestCase):
    def test_empty_selection_returns_all(self):
        self.assertEqual(len(apply_selection(EXERCISES, DEFS, {})), 4)

    def test_or_within_facet_and_across_facets(self):
        sel = {"muscles": ["chest", "biceps"]}
        self.assertEqual(names(apply_selection(EXERCISES, DEFS, sel)), ["bench", "fly", "curl"])
        sel["equipment"] = ["dumbbell"]
        self.assertEqual(names(apply_selection(EXERCISES, DEFS, sel)), ["fly", "curl"])

    def test_muscles_combine_primary_and_secondary(self):
        self.assertEqual(names(apply_selection(EXERCISES, DEFS, {"muscles": ["triceps"]})), ["bench"])

    def test_defaults_and_laterality(self):
        self.assertEqual(names(apply_selection(EXERCISES, DEFS, {"setCompletionMeasure": ["time"]})), ["fly"])
        self.assertEqual(len(apply_selection(EXERCISES, DEFS, {"setCompletionMeasure": ["reps"]})), 3)
        self.assertEqual(names(apply_selection(EXERCISES, DEFS, {"laterality": ["uni-lateral"]})), ["curl"])

    def test_counts_ignore_own_facet_but_respect_others(self):
        sel = {"muscles": ["chest"], "equipment": ["dumbbell"]}
        groups = {g["key"]: g for g in compute_facet_counts(EXERCISES, DEFS, sel)}
        muscles = {v["value"]: v["count"] for v in groups["muscles"]["values"]}
        # muscles counted against equipment=dumbbell only
        self.assertEqual(muscles, {"chest": 1, "biceps": 1})
        equipment = {v["value"]: v["count"] for v in groups["equipment"]["values"]}
        # equipment counted against muscles=chest only
        self.assertEqual(equipment, {"barbell": 1, "dumbbell": 1})

    def test_zero_count_hidden_but_selected_kept(self):
        sel = {"origin": ["custom"], "muscles": ["biceps"]}
        groups = {g["key"]: g for g in compute_facet_counts(EXERCISES, DEFS, sel)}
        origin = {v["value"]: v for v in groups["origin"]["values"]}
        self.assertEqual(set(origin), {"wger", "custom"})
        self.assertEqual(origin["custom"]["count"], 0)
        self.assertTrue(origin["custom"]["selected"])
        muscles = {v["value"] for v in groups["muscles"]["values"]}
        self.assertNotIn("abdominals", muscles)
        self.assertIn("chest", muscles)

    def test_missing_fields_are_ignored(self):
        groups = {g["key"]: g for g in compute_facet_counts(EXERCISES, DEFS, {})}
        total_origin = sum(v["count"] for v in groups["origin"]["values"])
        self.assertEqual(total_origin, 3)

    def test_parse_selection_and_chips(self):
        form = MultiDict([("facet_muscles", "Chest"), ("facet_muscles", "lower back"),
                          ("facet_origin", ""), ("search", "x")])
        sel = parse_selection(form, DEFS)
        self.assertEqual(sel, {"muscles": ["chest", "lower_back"]})
        chips = selected_chips(DEFS, sel)
        self.assertEqual([c["label"] for c in chips], ["Chest", "Lower Back"])

    def test_wrapped_listing_rows(self):
        rows = [{"entity": e} for e in EXERCISES]
        self.assertEqual(len(apply_selection(rows, DEFS, {"origin": ["wger"]})), 2)

    def test_custom_facetdef_scalar(self):
        f = FacetDef("k", "K", lambda e: e.get("k"))
        self.assertEqual(f.values({"k": "A b"}), ["a_b"])
        self.assertEqual(f.values({}), [])


class TestFacetPanelRendering(unittest.TestCase):
    def _render(self, template, **extra):
        from pathlib import Path
        from flask import Flask, render_template
        root = Path(__file__).resolve().parents[2]
        app = Flask(__name__, template_folder=str(root / 'common' / 'templates'))
        facet_vars = {}
        result_count = extra.pop('result_count', 2)
        if extra.pop('with_facets', False):
            items = [{"entity": e} for e in EXERCISES]
            sel = {"muscles": ["chest"]}
            facet_vars = dict(
                facet_groups=compute_facet_counts(items, DEFS, sel),
                facet_chips=selected_chips(DEFS, sel), facet_selected_total=1,
                facet_result_count=result_count, facet_form_prefix="facet_")
        with app.test_request_context():
            return render_template(
                template, entity_name='ExerciseTable', filter_terms=[],
                main_content_container='entities-container', entities_listing_route='/listing?',
                entities=[], fields_to_display={'listing_view': []}, view='list', page=1,
                total_pages=1, **facet_vars, **extra)

    def test_panel_hidden_without_facets(self):
        html = self._render('entity_list_component.html')
        self.assertNotIn('facet-groups', html)
        self.assertNotIn('Filters', html)

    def test_panel_shown_with_facets_and_no_push_url(self):
        html = self._render('entity_list_component.html', with_facets=True)
        self.assertIn('id="facet-groups-ExerciseTable"', html)
        self.assertIn('name="facet_muscles" value="chest"', html)
        self.assertIn('facet-chip', html)
        self.assertNotIn('hx-push-url', html)
        self.assertNotIn('hx-swap-oob', html.split('id="facet-groups-ExerciseTable"')[0].split('facet-chips')[0])

    def test_group_keys_are_stable_across_initial_and_oob_rendering(self):
        initial = self._render('entity_list_component.html', with_facets=True)
        updated = self._render('entity_results_partial.html', with_facets=True, facet_oob=True)
        groups = compute_facet_counts([{"entity": e} for e in EXERCISES], DEFS, {"muscles": ["chest"]})
        for group in groups:
            attribute = 'data-facet-group="{}"'.format(group['key'])
            self.assertIn(attribute, initial)
            self.assertIn(attribute, updated)

    def test_result_count_matches_sheet_button_on_initial_and_oob_rendering(self):
        for count in (0, 1, 2):
            text = '{} result{}'.format(count, '' if count == 1 else 's')
            for template, extra in (
                ('entity_list_component.html', {}),
                ('entity_results_partial.html', {'facet_oob': True}),
            ):
                with self.subTest(count=count, template=template):
                    html = self._render(template, with_facets=True, result_count=count, **extra)
                    self.assertIn('role="status">{}</span>'.format(text), html)
                    self.assertIn('Show {}'.format(text), html)

    def test_partial_returns_oob_fragments_only_when_requested(self):
        html = self._render('entity_results_partial.html', with_facets=True, facet_oob=True)
        for frag in ('facet-chips-', 'facet-groups-', 'facet-badge-', 'facet-show-'):
            self.assertIn(f'id="{frag}ExerciseTable"', html)
        self.assertIn('Show 2 results', html)
        plain = self._render('entity_results_partial.html', with_facets=True, facet_oob=False)
        self.assertNotIn('facet-groups-', plain)


if __name__ == "__main__":
    unittest.main()
