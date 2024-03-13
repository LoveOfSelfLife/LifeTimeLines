from common.entity_store import EntityObject
class SyncOperation (EntityObject):
    table_name='SyncOperationTable'
    partition_value="photos"
    key_field="id"
    fields=["id", "status", "num_items_processed"]

    def __init__(self, d={}):
        super().__init__(d)

