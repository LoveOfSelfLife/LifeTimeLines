
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
    entity_key = entity.get_key_value()
    if entity_key is None:
        return

    partition_value = get_partition_value_for_favorite(table_name, member_id)

    favored_entity = FavoritesEntity({"entity_id": entity_key, "entity_type_and_member_id": partition_value})
    es.upsert_item(favored_entity)

def is_entity_a_favorite(entity, member_id):
    entity_key = entity.get_key_value()
    if entity_key is None:
        return False

    favorite_ids = get_all_favorite_entity_ids(entity.table_name, member_id)
    return entity_key in favorite_ids

def remove_entity_from_favorites(entity, member_id):
    es = EntityStore()
    table_name = entity.table_name
    partition_value = get_partition_value_for_favorite(table_name, member_id)
    entity_key = entity.get_key_value()

    favored_entity = FavoritesEntity({"entity_id": entity_key, "entity_type_and_member_id": partition_value})
    e = es.get_item(favored_entity)
    if e is None:
        return False

    es.delete_item(favored_entity)
    return True


def toggle_entity_favorite(entity, member_id):
    """Toggle favorite state and return True if favorite is active after the toggle."""
    if is_entity_a_favorite(entity, member_id):
        remove_entity_from_favorites(entity, member_id)
        return False

    add_entity_to_favorites(entity, member_id)
    return True


def get_all_favorite_entity_ids(table_name, member_id):
    """Get all entity IDs that are favorites for a specific member and table type"""
    from common.entity_store import EntityStore
    
    es = EntityStore()
    partition_value = get_partition_value_for_favorite(table_name, member_id)
    
    # Query all favorites for this member and entity type
    # favorites_entities = es.get_items_by_partition_key(FavoritesEntity.table_name, partition_value)
    favorites_entities = list(es.list_items(FavoritesEntity({"entity_type_and_member_id": partition_value})))
    sorted_favorites = sorted(favorites_entities, key=lambda x: x.get('Timestamp', 0), reverse=True)  # Sort by Timestamp descending
    # Extract just the entity IDs
    favorite_ids = [fav.get('entity_id') for fav in sorted_favorites if fav]
    return favorite_ids

