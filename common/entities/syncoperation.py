from common.entity_object import EntityObject
class SyncOperation (EntityObject):
    table_name='SyncOperationTable'
    partition_value="photos"
    key_field="id"
    fields=["id", "status", "num_items_processed"]

    def __init__(self, d={}):
        super().__init__(d)


class ConsumedItemsTimeTracker (EntityObject):
    table_name='ConsumedItemsTrackerTable'
    partition_field="consumer_id"
    key_field="table_name"
    fields=["consumer_id", "table_name", "latest_item_consumed_iso"]

    def __init__(self, d={}):
        super().__init__(d)

class LatestItemUpdatedTimeTracker (EntityObject):
    table_name='LatestItemsUpdatedTrackerTable'
    partition_value="all"
    key_field="table_name"
    fields=["table_name", "latest_item_updated_iso"]

    def __init__(self, d={}):
        super().__init__(d)

