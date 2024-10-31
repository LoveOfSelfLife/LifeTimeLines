from common.entity_store import EntityObject

class MediaItemDay (EntityObject):
    table_name="MediaItemDayTable"
    fields=["day", "item", "creationTime", "mimeType"]
    key_field="item"
    partition_field="day"

    def __init__(self, d={}):
        super().__init__(d) 
