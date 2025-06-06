from common.entity_store import EntityStore, EntityObject
from common.entity_consumer import get_iso_timestamp_of_latest_stored_item_in_table


class EntityStoreCache:
    """_summary__
    Entity store cache:

    Instances of this class will cache the list of objects retrieved from the entity storage, which is built 
    on top of azure table storage.

    An instance of this class will be initialized with the name of the entity store, and then the instance 
    will retrieve all of the items from the underlying entity store and store the items in a list.  The initializer 
    will also read the value of the timestamp of when the latest item that has been updated in the entity store, 
    whether it be added or updated.  This timestamp is stored in its own entity store table, and the value is 
    updated whenever somethng changes in the entity store of interest.

    Now any client component that needs access to the list of objects, does not need to go to the underlying 
    storage, but rather can access the elements from the cached list.   however, before any client accesses 
    the cached list, the handler will first check if the latest item timestamp of the underlying entity has not 
    chaned since it was last read.  If it has changed, then the cache needs to be refreshed, as was done during 
    initialization.be to     
    """
    
    def __init__(self, entity_to_cache:EntityObject, partition_key=None):
        self.entity_to_cache = entity_to_cache
        self.partition_key = partition_key
        self.items = []
        self.items_map = {}
        # self.items_composite_key_map = {}
        self.entity_store = EntityStore()
        self.latest_item_updated_iso = None
        if self.entity_to_cache.get_static_partition_value():
            self.partition_key = self.entity_to_cache.get_static_partition_value()
        else:
            if not self.partition_key:
                raise ValueError("Partition key must be provided for non-static partitioned entities.")
        self.entity_to_cache.set_partition_value(self.partition_key)
        self._refresh_cache()  # Initialize the cache by loading items from the entity store

    def _refresh_cache(self):
        """Refresh the cache by loading items from the entity store."""
        # Get the latest item updated timestamp from the entity store
        self.latest_item_updated_iso = get_iso_timestamp_of_latest_stored_item_in_table(self.entity_to_cache.get_table_name())
        self.items = self.entity_store.list_items(self.entity_to_cache)
        self.items = list(self.items)
        self.items_map = {item.get_key_value(): item for item in self.items}

    def get_items(self):
        """Get the cached items. If the latest item updated timestamp has changed, refresh the cache."""
        # Check if the latest item updated timestamp has changed
        latest_item_updated_iso = get_iso_timestamp_of_latest_stored_item_in_table(self.entity_to_cache.get_table_name())
        if latest_item_updated_iso != self.latest_item_updated_iso:
            self._refresh_cache()
        return self.items

    def get_item_by_key(self, key):
        """Get an item by its key from the cached items."""
        return self.items_map.get(key, None)
        
    def delete_item(self, item:EntityObject):
        """Delete an item from the entity store and refresh the cache."""
        self.entity_store.delete_items([item])
        self._refresh_cache()
    