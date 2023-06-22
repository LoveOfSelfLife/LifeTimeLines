from common.entities.entity import EntityObject


class SyncOperation (EntityObject):
    table_name='SyncOperationTable'
    partition="photos"
    key="id"
    fields=["status", "num_items_processed"]

    def __init__(self, d):
        super().__init__(d)