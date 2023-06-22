from common.entities.entity import EntityObject


class PhotosDateRanges (EntityObject):
    table_name="DateRangesTable"
    partition="photos"
    key="id"
    fields=["Start", "End"]

    def __init__(self, d):
        super().__init__(d)


class MediaItem (EntityObject):
    table_name='MediaItemsTable'
    partition="media_item"
    key="id"
    fields=["creationTime", "mimeType"]

    def __init__(self, d):
        super().__init__(d)