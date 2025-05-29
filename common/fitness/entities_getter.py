from common.entity_store_cache import EntityStoreCache


entity_store_cache_dict = {}
def get_list_of_entities(entity_name, filter_func=None, filter_term=None):
    global entity_store_cache_dict
    from common.fitness.active_fitness_registry import get_fitnessclub_entity_type_for_entity
    entity_type = get_fitnessclub_entity_type_for_entity(entity_name)

    if entity_store_cache_dict.get(entity_name, None) is None:
        entity_store_cache_dict[entity_name] = EntityStoreCache(entity_type)

    entities = entity_store_cache_dict[entity_name].get_items()

    if filter_func:
        return filter_func(entities, filter_term)
    else:
        return entities


def get_filtered_entities(entity_name, fields_to_display, filter_func=None, filter_term=None):

    filtered_entities = get_list_of_entities(entity_name, filter_func, filter_term)
    # if not fields_to_display:
    #     fields_to_display = get_fitnessclub_listing_fields_for_entity(entity_name)

    entities = []
    for e in filtered_entities:
        field_values = [e.get(f, None) for f in fields_to_display]
        key = e.get_composite_key()
        entities.append({"key": key, "field_values": field_values})
    return entities


def delete_entity(entity):
    entity_store_cache_dict[entity.get_table_name()].delete_item(entity)

def get_entity(entity_name, key):
    global entity_store_cache_dict
    from common.fitness.active_fitness_registry import get_fitnessclub_entity_type_for_entity
    if entity_store_cache_dict.get(entity_name, None) is None:
        entity_store_cache_dict[entity_name] = EntityStoreCache(get_fitnessclub_entity_type_for_entity(entity_name))

    return entity_store_cache_dict[entity_name].get_item_by_key(key)
