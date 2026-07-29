import re

from common.entity_store_cache import EntityStoreCache
from common.fitness.active_fitness_registry import get_entity_obj_from_entity_name
from common.fitness.favorites_entity import get_all_favorite_entity_ids
entity_store_cache_dict = {}

def get_entities(entity_name, fields_to_display, filter_term=None, partition_key=None, sort_by='name', sort_ascending=True, member_id=None):


    if filter_term:
        if isinstance(filter_term, str):
            import ast
            filter_term = ast.literal_eval(filter_term)

    filtered_entities = get_filtered_entities(entity_name, filter_term, partition_key, sort_by, sort_ascending, member_id=member_id)
    favorite_entity_ids = set()
    if member_id:
        favorite_entity_ids = get_all_favorite_entity_ids(entity_name, member_id)

    entities = []
    for e in filtered_entities:
        field_values = [e.get(f, None) for f in fields_to_display['listing_view']]
        key = e.get_composite_key()
        entity_id = e.get_key_value()

        card_view_field_values = None
        if fields_to_display['card_view']:
            card_view_field_values = {}
            for field,lmbda in fields_to_display['card_view'].items():
                card_view_field_values[field] = lmbda(e) if lmbda else None
        entities.append({
            "key": key,
            "field_values": field_values,
            "entity": e,
            "entity_id": entity_id,
            "is_favorite": entity_id in favorite_entity_ids,
            "card_view_fields": card_view_field_values
        })
    return entities


def _matches_single_pattern_term(entity, term):
    """Check if a single pattern term matches the entity."""
    if ':' in term:
        # Attribute filter: "equip:bar"
        attr_part, value_part = term.split(':', 1)
        attr_part = attr_part.strip()
        value_part = value_part.strip()
        # Find attribute where attr_part is a substring of the attribute name
        for key, value in entity.items():
            if attr_part in key.lower():
                if value_part in str(value).lower():
                    return True
        return False
    else:
        # Value filter: search all string attributes
        for key, value in entity.items():
            if isinstance(value, str) or isinstance(value, list):
                if term in str(value).lower():
                    return True
        return False


def matches_text_pattern_filter(entity, pattern_str):
    """
    Match entity against a pattern string with the following rules:
    - '+' or 'and': AND logic - all connected terms must match
    - 'or' or '|': OR logic - any separated group can match (OR has higher precedence)
    - 'attr:value' format: search for attr in attribute names and value in attribute values
    - plain text: search all string-valued attributes

    Examples:
    - "ace" matches if any string attribute contains "ace"
    - "ace+push" or "ace and push": matches if one attribute contains "ace" AND another contains "push"
    - "ace or push" or "ace | push": matches if any attribute contains "ace" OR "push"
    - "equip:bar": matches if an attribute name contains "equip" and its value contains "bar"
    - "ace and equip:bar or test": matches if ace AND (equip:bar OR test)
    """
    if not pattern_str:
        return True

    if entity.get("id", None) == 'ace_62':
        pass

    pattern_str = pattern_str.lower().strip()

    # Split by AND ('+' or 'and', case-insensitive)
    and_groups = re.split(r'\+|\s+and\s+', pattern_str)

    # AND logic - all groups must match
    for and_group in and_groups:
        and_group = and_group.strip()
        # Within each AND group, check OR logic
        # Split by 'or' or '|' (case-insensitive for 'or')
        or_terms = re.split(r'\s+or\s+|\|', and_group)

        # OR logic - at least one term must match
        any_match = False
        for term in or_terms:
            term = term.strip()
            if term and _matches_single_pattern_term(entity, term):
                any_match = True
                break

        if not any_match:
            return False

    return True

def _matches_special_filter_term(entity, term_type, pattern):
    """
    Delegate special term matching (e.g. ^section, ^related) to the
    externally-implemented special matcher.
    """
    from common.fitness.hx_common import entity_matches_special_term
    
    return entity_matches_special_term(entity, term_type, pattern)

def matches_all_terms_in_filter(entity, filter_term, member_id=None, favorite_entity_ids=None):
    # check if filter_term is a string, in which case convert it to a python object
    # using ast.literal_eval
    if filter_term and isinstance(filter_term, str):
        import ast
        filter_term = ast.literal_eval(filter_term)

    if filter_term is None:
        return True

    for term in filter_term:
        # Skip non-filter metadata entries (e.g. {"summary": ...})
        if not isinstance(term, dict):
            continue

        pattern = term.get("value", None)
        term_type = term.get("type", None)

        # Ignore terms with no type/value payload
        if term_type is None or pattern is None or pattern == "":
            continue

        if term_type == "text":
            pattern = pattern.lower()
            if matches_text_pattern_filter(entity, pattern):
                continue
            return False

        if term_type == "favorites":
            if favorite_entity_ids is not None:
                entity_id = entity.get(entity.key_field)
                if entity_id not in favorite_entity_ids:
                    return False
            continue

        # New behavior: special terms beginning with '^'
        if isinstance(term_type, str) and term_type.startswith("^"):
            if _matches_special_filter_term(entity, term_type, pattern):
                continue
            return False

        # Unknown term types are ignored for backward compatibility

    return True


def is_entity_hidden(entity):
    """Filter out entities that are marked as "hide" 
    """
    hide = entity.get("hide", None)
    return hide


def generic_entity_filter(entities, filter_term, member_id=None, favorite_entity_ids=None):
    # filter_term is a list of dictionaries
    # each dictionary has an id and a value
    # for example: [{"id": "text", "value": "squat"}, {"id": "category", "value": "core"}]
    # in order for an entity from the list of entities to be included in the result
    # it must match all the filter terms where the value for that filter term is not empty
    # if the value for a filter term is empty, it is ignored
    #
    # first remove all entities that are hidden
    entities = [e for e in entities if not is_entity_hidden(e)]

    if filter_term is None:
        return entities
    if len(filter_term) == 0:
        return entities
    filtered_entities = []
    for entity in entities:
        if matches_all_terms_in_filter(entity, filter_term, member_id=member_id, favorite_entity_ids=favorite_entity_ids):
            filtered_entities.append(entity)
    return filtered_entities


def get_filtered_entities(entity_name, filter_term=None, partition_key=None, sort_by='name', sort_ascending=True, member_id=None):
    global entity_store_cache_dict

    entity_type = get_entity_obj_from_entity_name(entity_name)
    cache_key = get_cache_key(entity_type, partition_key)

    if entity_store_cache_dict.get(cache_key, None) is None:
        entity_store_cache_dict[cache_key] = EntityStoreCache(entity_type, partition_key=partition_key)

    entities = entity_store_cache_dict[cache_key].get_items()

    if filter_term:
        # Check if favorites filter is present - if so, pre-load all favorites for better performance
        favorites_filter = None
        for term in filter_term:
            if term.get('type') == 'favorites':
                favorites_filter = term
                break
        
        if favorites_filter and member_id:
            # Pre-load all favorite entity IDs for this member and entity type
            favorite_entity_ids = get_all_favorite_entity_ids(entity_type.table_name, member_id)
            entities = generic_entity_filter(entities, filter_term, member_id=member_id, favorite_entity_ids=favorite_entity_ids)
        else:
            entities = generic_entity_filter(entities, filter_term, member_id=member_id)

    if sort_by and sort_by in entity_type.get_fields():
        entities = sorted(entities, key=lambda x: x.get(sort_by).lower() if x.get(sort_by) else x.get(sort_by, ''), reverse=not sort_ascending)
    return entities

def get_cache_key(entity_type, partition_key=None):
    if entity_type.get_static_partition_value():
        cache_key = entity_type.get_table_name()
    else:
        if not partition_key:
            raise ValueError("Partition key must be provided for non-static partitioned entities.")
        cache_key = entity_type.get_table_name() + f"_{partition_key}"
    return cache_key

def delete_entity(entity, partition_key=None):
    global entity_store_cache_dict
    cache_key = get_cache_key(entity, partition_key)
    entity_store_cache_dict[cache_key].delete_item(entity)

def get_entity(entity_name, key, partition_key=None, member_id=None):
    global entity_store_cache_dict

    entity = get_entity_obj_from_entity_name(entity_name)
    cache_key = get_cache_key(entity, partition_key)
    if entity_store_cache_dict.get(entity_name, None) is None:
        entity_store_cache_dict[entity_name] = EntityStoreCache(get_entity_obj_from_entity_name(entity_name))

    return entity_store_cache_dict[entity_name].get_item_by_key(key)

def get_entity2(entity, key, partition_key=None):
    global entity_store_cache_dict

    cache_key = get_cache_key(entity, partition_key)
    if entity_store_cache_dict.get(cache_key, None) is None:
        entity_store_cache_dict[cache_key] = EntityStoreCache(entity, partition_key)
    return entity_store_cache_dict[cache_key].get_item_by_key(key)


def matches_filter(entity,term):
    if term is None:
        return True
    term = term.lower()
    terms = term.split()
    for t in terms:
        for field in entity.get_fields():
            if field in entity and isinstance(entity[field], str):
                if t in entity[field].lower():
                    return True
    return False
