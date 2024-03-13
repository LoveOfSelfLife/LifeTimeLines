from common.entity_store import EntityObject
class AlbumSyncTime (EntityObject):
    """ this table has a record for each album
    where the record has the timestamp of the latest photo sync'ed from that album
    """
    table_name='AlbumSyncTimeTable'
    fields=["albumId", "latestPhotoInAlbumTime"]
    key_field="albumId"
    partition_value="album"

    def __init__(self, d={}):
        super().__init__(d)

class AlbumItem (EntityObject):
    """this table has a separate partion for each album, so the partitionKey is the album id
    the records within that partition represent each mediaItem contained in that album
    creationTime is the time that the mediaItem was created
    """
    table_name='AlbumItemTable'
    fields=["mitemId", "albumId", "creationTime"]
    key_field="mitemId"
    partition_field="albumId"

    def __init__(self, d={}):
        super().__init__(d)
