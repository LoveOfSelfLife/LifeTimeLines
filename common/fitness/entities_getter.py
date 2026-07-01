from common.entity_store_cache import EntityStoreCache
from common.fitness.active_fitness_registry import get_entity_obj_from_entity_name
from common.fitness.exercise_entity import generic_entity_filter
from common.fitness.favorites_entity import get_all_favorite_entity_ids
entity_store_cache_dict = {}

def get_entities(entity_name, fields_to_display=None, filter_term=None, partition_key=None, sort_by='name', sort_ascending=True, member_id=None):

    filtered_entities = get_filtered_entities(entity_name, filter_term, partition_key, sort_by, sort_ascending, member_id=member_id)

    entities = []
    for e in filtered_entities:
        field_values = [e.get(f, None) for f in fields_to_display['listing_view']] if fields_to_display and fields_to_display['listing_view'] else None
        key = e.get_composite_key()

        card_view_field_values = None
        if fields_to_display and fields_to_display['card_view']:
            card_view_field_values = {}
            for field,lmbda in fields_to_display['card_view'].items():
                card_view_field_values[field] = lmbda(e) if lmbda else None
        entities.append({"key": key, "field_values": field_values, "entity": e, "card_view_fields": card_view_field_values})
    return entities


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
