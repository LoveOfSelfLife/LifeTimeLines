from common.entities.entity import EntityObject

class SyncTime (EntityObject):
    table_name='SyncTimesTable'
    partition="album"
    key="albumId"
    fields=["albumId", "lastSyncDateTime"]

    def __init__(self, d):
        super().__init__(d)

class AlbumItem (EntityObject):
    table_name='AlbumItemsTable'
    partition="album"
    key="mitemId"
    fields=["mitemId", "albumId", "creationTime"]

    def __init__(self, d):
        super().__init__(d)