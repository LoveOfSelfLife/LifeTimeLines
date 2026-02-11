
from common.entity_store import EntityObject, EntityStore

class FavoritesEntity (EntityObject):
    """_summary_
        used to represent that an entity is a favorite for a member
        entity_id is the id of the entity that is marked as favorite, for example, it can be an exercise id, or a program id, etc.
        entity_type_and_member_id is a combination of the entity type and the member id, 
        for example, "ExerciseTable-12345" or "MemberProgramTable-12345", etc. 
        This is used as the partition key to group all favorites of a member together.
    """
    table_name="FavoritesTable"
    fields=["entity_id", "entity_type_and_member_id"]
    key_field="entity_id"
    partition_field="entity_type_and_member_id"

    def __init__(self, d={}):
        super().__init__(d)


def get_partition_value_for_favorite(entity_table_name, member_id):
    return f"{entity_table_name}-{member_id}"

def add_entity_to_favorites(entity, member_id):
    es = EntityStore()
    table_name = entity.table_name
    entity_key = entity.get(entity.key_field, None)
    if entity_key is None:
        return

    partition_value = get_partition_value_for_favorite(table_name, member_id)

    favored_entity = FavoritesEntity({"entity_id": entity_key, "entity_type_and_member_id": partition_value})
    es.upsert_item(favored_entity)

def is_entity_a_favorite(entity, member_id):
    table_name = FavoritesEntity.table_name
    partition_value = get_partition_value_for_favorite(table_name, member_id)
    from common.fitness.entities_getter import get_filtered_entities
    favs = get_filtered_entities(table_name, filter_term=None, partition_key=partition_value, member_id=member_id)
    favored_entity = FavoritesEntity({"entity_id": entity.get(entity.key_field), "entity_type_and_member_id": partition_value})
    return favored_entity in favs

def remove_entity_from_favorites(entity, member_id):
    es = EntityStore()
    table_name = entity.table_name
    entity_key = entity.key_field

    favored_entity = FavoritesEntity({"entity_id": entity_key, "entity_type_and_member_id": partition_value})
    e = es.get_item(favored_entity)
    return e is not None


def get_all_favorite_entity_ids(table_name, member_id):
    """Get all entity IDs that are favorites for a specific member and table type"""
    from common.entity_store import EntityStore
    
    es = EntityStore()
    partition_value = get_partition_value_for_favorite(table_name, member_id)
    
    # Query all favorites for this member and entity type
    # favorites_entities = es.get_items_by_partition_key(FavoritesEntity.table_name, partition_value)
    favorites_entities = es.list_items(FavoritesEntity({"entity_type_and_member_id": partition_value}))
    
    # Extract just the entity IDs
    favorite_ids = {fav.get('entity_id') for fav in favorites_entities if fav}
    return favorite_ids

