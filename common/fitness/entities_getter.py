from common.entity_store_cache import EntityStoreCache

entity_store_cache_dict = {}

# TODO: need to refactor this to combine filter_func and filter_term_func into a single function
# and remove the need for filter_term
def get_list_of_entities(entity_name, filter_func=None, filter_term=None, partition_key=None):
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

def get_filtered_entities(entity_name, fields_to_display, filter_func=None, filter_term=None, partition_key=None):

    filtered_entities = get_list_of_entities(entity_name, filter_func, filter_term, partition_key)

    entities = []
    for e in filtered_entities:
        field_values = [e.get(f, None) for f in fields_to_display]
        key = e.get_composite_key()
        entities.append({"key": key, "field_values": field_values, "entity": e})
    return entities


def delete_entity(entity):
    entity_store_cache_dict[entity.get_table_name()].delete_item(entity)

def get_entity(entity_name, key):
    global entity_store_cache_dict
    from common.fitness.active_fitness_registry import get_fitnessclub_entity_type_for_entity
    if entity_store_cache_dict.get(entity_name, None) is None:
        entity_store_cache_dict[entity_name] = EntityStoreCache(get_fitnessclub_entity_type_for_entity(entity_name))

    return entity_store_cache_dict[entity_name].get_item_by_key(key)
