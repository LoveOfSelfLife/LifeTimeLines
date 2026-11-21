"""Generic faceted-search support.

A facet is a named dimension of an entity (e.g. muscles, equipment). Each facet
extracts zero or more string values from an entity. Selection semantics are:
OR within a facet, AND across facets. Facet counts are "disjunctive": the counts
for a facet ignore that facet's own selection so it can still be broadened.
"""
from collections import Counter

FACET_FORM_PREFIX = "facet_"


class FacetDef:
    def __init__(self, key, label, extract, value_label=None):
        self.key = key
        self.label = label
        self._extract = extract
        self._value_label = value_label

    def values(self, entity):
        raw = self._extract(entity)
        if raw is None:
            return []
        if isinstance(raw, (str, bool, int, float)):
            raw = [raw]
        seen = []
        for v in raw:
            if v is None or v == "":
                continue
            s = normalize_value(v)
            if s and s not in seen:
                seen.append(s)
        return seen

    def display(self, value):
        if self._value_label:
            return self._value_label(value)
        return value.replace("_", " ").title()


def normalize_value(value):
    return str(value).strip().lower().replace(" ", "_")


def _entity_of(item):
    # Listing rows from get_entities() wrap the entity: {"entity": e, ...}
    if isinstance(item, dict) and "entity" in item:
        return item["entity"]
    return item


def parse_selection(form, facet_defs):
    """Read the selection from a form/args mapping (names are facet_<key>)."""
    selection = {}
    for f in facet_defs:
        name = FACET_FORM_PREFIX + f.key
        getlist = getattr(form, "getlist", None)
        raw = getlist(name) if getlist else form.get(name, [])
        if isinstance(raw, str):
            raw = [raw]
        vals = [normalize_value(v) for v in raw if v not in (None, "")]
        if vals:
            selection[f.key] = list(dict.fromkeys(vals))
    return selection


def _matches(entity, facet_defs, selection, skip_key=None):
    for f in facet_defs:
        wanted = selection.get(f.key)
        if not wanted or f.key == skip_key:
            continue
        if not set(wanted).intersection(f.values(entity)):
            return False
    return True


def apply_selection(items, facet_defs, selection):
    if not selection:
        return list(items)
    return [i for i in items if _matches(_entity_of(i), facet_defs, selection)]


def compute_facet_counts(items, facet_defs, selection):
    """Return [{key, label, values: [{value, label, count, selected}]}].

    Values are sorted by display label, ignoring case. Values with a zero count
    are omitted, except that currently selected values are kept so they can be unchecked.
    """
    selection = selection or {}
    groups = []
    for f in facet_defs:
        counter = Counter()
        for item in items:
            entity = _entity_of(item)
            if _matches(entity, facet_defs, selection, skip_key=f.key):
                counter.update(f.values(entity))
        selected = set(selection.get(f.key, []))
        values = [
            {"value": v, "label": f.display(v), "count": c, "selected": v in selected}
            for v, c in counter.items() if c > 0
        ]
        present = {v["value"] for v in values}
        values.extend(
            {"value": v, "label": f.display(v), "count": 0, "selected": True}
            for v in selected if v not in present
        )
        values.sort(key=lambda v: (v["label"].casefold(), v["value"]))
        if values:
            groups.append({"key": f.key, "label": f.label, "values": values,
                           "selected_count": len(selected)})
    return groups


def selected_chips(facet_defs, selection):
    chips = []
    for f in facet_defs:
        for v in (selection or {}).get(f.key, []):
            chips.append({"key": f.key, "value": v, "group": f.label, "label": f.display(v)})
    return chips


def build_facet_context(entity_name, items_before_facets, form):
    """Return (items_after_facets, template_vars) or (items, {}) if facets are disabled."""
    from common.fitness.facets import get_fitnessclub_facets_for_entity
    facet_defs = get_fitnessclub_facets_for_entity(entity_name)
    if not facet_defs:
        return items_before_facets, {}
    selection = parse_selection(form, facet_defs)
    filtered = apply_selection(items_before_facets, facet_defs, selection)
    return filtered, {
        "facet_groups": compute_facet_counts(items_before_facets, facet_defs, selection),
        "facet_chips": selected_chips(facet_defs, selection),
        "facet_selected_total": sum(len(v) for v in selection.values()),
        "facet_result_count": len(filtered),
        "facet_form_prefix": FACET_FORM_PREFIX,
    }
