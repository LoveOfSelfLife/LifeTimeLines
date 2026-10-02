

from flask import request, session


import ast


def get_requested_favorites_only_from_request():
    if request.method == 'POST':
        favorites_only = request.form.get('favorites_only')
    else:
        favorites_only = request.args.get('favorites_only')

    if favorites_only is None:
        return None

    return str(favorites_only).lower() == 'true'


def resolve_favorites_filter_terms(filter_terms, requested_favorites_only=None, session_favorites_only=False):
    existing_favorites_only = None
    normalized_filter_terms = []

    for term in filter_terms:
        if isinstance(term, dict) and term.get('type') == 'favorites':
            existing_favorites_only = str(term.get('value', '')).lower() == 'true'
            continue

        normalized_filter_terms.append(term)

    if requested_favorites_only is not None:
        favorites_only = requested_favorites_only
    elif existing_favorites_only is not None:
        favorites_only = existing_favorites_only
    else:
        favorites_only = session_favorites_only

    if favorites_only:
        normalized_filter_terms.append({
            'type': 'favorites',
            'value': 'true'
        })

    return normalized_filter_terms, favorites_only


def add_filter_terms_summary(filter_terms):
    """
    Given a list of filter terms, generate a summary of the filter terms for display.
    This function can be expanded to create more user-friendly summaries based on the filter types.
    """
    summary_terms = []
    for term in filter_terms:
            if not isinstance(term, dict):
                continue

            term_type = term.get('type')
            term_value = term.get('value')

            # Skip non-filter terms like {'summary': '...'} and favorites helper terms.
            if not term_type or term_type == 'favorites' or term_value is None:
                continue

            summary_terms.append(f"{term_type}:{term_value} ")

    return [{ "summary":" ".join(summary_terms).strip() }] if summary_terms else []


def preprocess_search_term(search_term):
    # search term is a string.  If it starts with "^section:" or "^related:", we convert it to a filter term where
    # the text after the prefix is treated as a value for the filter term
    # after processing the special prefix filter term, the remainder of the text is treated as a single text filter term
    # we then return both the special prefix filter term and the text filter term as a list of filter terms
    # examples, 1. given "arms and equip:barbell" would return [, {"type": "text", "value": "and equip:barbell"}]
    # 2. given "^section:arms and equip:barbell" would return [{"type": "section", "value": "arms"}, {"type": "text", "value": "and equip:barbell"}]
    # 3. given "^related:12345 and equip:barbell" would return [{"type": "related", "value": "12345"}, {"type": "text", "value": "and equip:barbell"}]
    # 4. given "^section:arms" would return [{"type": "section", "value": "arms"}]
    # 5. given "^section:core ^related:12345" would return [{"type": "section", "value": "core"}, {"type": "related", "value": "12345"}]
    # 6. given "^section:core ^related:12345 and equip:barbell" would return [{"type": "section", "value": "core"}, {"type": "related", "value": "12345"}, {"type": "text", "value": "and equip:barbell"}]

    # we can implement this by marching down the string, looking for special prefixes, and extracting the value after the prefix until we hit a space or the end of the string
    # if we hit a space, we recursively call this function on the remainder of the string after the space, and append the results to the list of filter terms
    filter_terms = []
    # first trim the left side of the string to remove any leading spaces
    search_term = search_term.lstrip()
    if search_term.startswith("^"):
        # get the prefix and value of the prefix up to the space or end of string
        prefix_end = search_term.find(":")
        prefix = search_term[0:prefix_end]
        value_end = search_term.find(" ", prefix_end)
        if value_end == -1:
            value = search_term[prefix_end + 1:]
            remainder = ""
        else:
            value = search_term[prefix_end + 1:value_end]
            remainder = search_term[value_end + 1:]

        filter_terms.append({
            "type": prefix,
            "value": value
        })
        if remainder:
            filter_terms.extend(preprocess_search_term(remainder))
        return filter_terms
    # if no special prefix, return the whole search term as a text filter term
    return [{"type": "text", "value": search_term}]


def get_filter_terms_from_request():
    """Extract search term from either POST form data or GET query parameters."""
    # Get search term from appropriate source
    search_term = ""
    filter_terms = []
    if request.method == 'POST':
        search_term = request.form.get("search", "").lower()
    else:
        # Try filter parameter first, then search parameter
        filter_param = request.args.get('filter', '')
        # if filter_param is present and is a string, need to convert it to a python object
        # using ast.literal_eval
        if filter_param and isinstance(filter_param, str):
            import ast
            filter_param = ast.literal_eval(filter_param)

        if len(filter_param) > 0:
            filter_terms = filter_param

        search_term = request.args.get('search', '')

    if search_term:
        # preprocess the search term to handle special cases like "section:" or "related:"
        filter_terms = filter_terms + preprocess_search_term(search_term)
        filter_terms = filter_terms + add_filter_terms_summary(filter_terms)

    requested_favorites_only = get_requested_favorites_only_from_request()
    session_favorites_only = session.get('favorites_preference', False)
    filter_terms, favorites_only = resolve_favorites_filter_terms(
        filter_terms,
        requested_favorites_only=requested_favorites_only,
        session_favorites_only=session_favorites_only,
    )
    session['favorites_preference'] = favorites_only

    return filter_terms


def parse_listing_filter(filter_param):

        # if filter_param is present and is a string, need to convert it to a python object
        # using ast.literal_eval
    if filter_param and isinstance(filter_param, str):
        import ast
        current_listing_filter = ast.literal_eval(filter_param)
    else:
        current_listing_filter = []
    return current_listing_filter


def entity_matches_special_term(entity, term_type, pattern):
    """
    Check if the given entity matches the special term based on its type and pattern.
    """
    # Implement the actual matching logic here based on your application's requirements
    # For example, if term_type is "^section", check if it makes sense to allow this entity in this section
    # If term_type is "^related", then the pattern will be the exercise id, so we check if the entity is related to that exercise
    # Return True if it matches, False otherwise

    from common.fitness.entities_getter import get_entity
    from common.fitness.exercise_entity import does_exercise_belong_in_section
    if term_type == "^section":
        section_type = pattern.strip()
        return does_exercise_belong_in_section(entity, section_type)
    elif term_type == "^related":
        from common.fitness.exercise_entity import are_these_exercises_related

        # the pattern in this case is expected to be an exercise id, so we should retrive the exercise and check if the entity is related to that exercise
        exercise_id = pattern.strip()
        exercise = get_entity("ExerciseTable", exercise_id)
        return are_these_exercises_related(entity, exercise)

    return False