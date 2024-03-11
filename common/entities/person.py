from common.entity_store import EntityObject
from common.utils import IDGenerator

class PersonEntity (EntityObject):
    table_name="EntityTable"
    fields=["id", "sms", "email", "aliases", "photos_album"]
    key_field="id"
    partition_value="persons"

    def __init__(self, d={}):
        super().__init__(d)


class GenericEntity (EntityObject):
    table_name="EntityTable"
    fields=["id", "type", "sms", "email", "aliases", "photos_album"]
    key_field="id"
    partition_field="type"

    def __init__(self, d={}):
        super().__init__(d)
