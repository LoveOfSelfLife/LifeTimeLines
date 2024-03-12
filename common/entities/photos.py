from common.entity_object import EntityObject

class PhotosDateRanges (EntityObject):
    table_name="PhotosDateRangesTable"
    fields=["startDate", "endDate"]
    key_field="startDate"
    partition_value="photos"

    def __init__(self, d={}):
        super().__init__(d)


class MediaItem (EntityObject):
    table_name='MediaItemsTable'
    fields=["mitemId", "creationTime", "mimeType"]
    key_field="mitemId"
    partition_value="media_item"

    def __init__(self, d={}):
        super().__init__(d)