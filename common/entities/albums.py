from common.entities.entity import EntityObject

class SyncTime (EntityObject):
    table_name='SyncTimesTable'
    partition_value="album"
    key_field="albumId"
    fields=["albumId", "lastSyncDateTime"]

    def __init__(self, d):
        super().__init__(d)

class AlbumItem (EntityObject):
    table_name='AlbumItemsTable'
    partition_field="albumId"
    key_field="mitemId"
    fields=["mitemId", "albumId", "creationTime"]

    def __init__(self, d):
        super().__init__(d)