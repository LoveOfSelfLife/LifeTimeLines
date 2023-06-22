from common.entities.entity import EntityObject


class PhotosDateRanges (EntityObject):
    table_name="DateRangesTable"
    partition_value="photos"
    key_field="id"
    fields=["id", "Start", "End"]

    def __init__(self, d):
        super().__init__(d)


class MediaItem (EntityObject):
    table_name='MediaItemsTable'
    partition_value="media_item"
    key_field="id"
    fields=["id", "creationTime", "mimeType"]

    def __init__(self, d):
        super().__init__(d)