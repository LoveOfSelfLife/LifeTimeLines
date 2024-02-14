from common.entity_store import EntityObject


class SyncOperation (EntityObject):
    table_name='SyncOperationTable'
    partition_value="photos"
    key_field="id"
    fields=["id", "status", "num_items_processed"]

    def __init__(self, d={}):
        super().__init__(d)

class LastSyncTimeTracker (EntityObject):
    table_name='SyncTimesTable'
    partition_field="consumer_id"
    key_field="table_name"
    fields=["consumer_id", "table_name", "last_sync_time", "last_sync_status", "last_sync_error", "last_sync_items_processed"]

    def __init__(self, d={}):
        super().__init__(d)

