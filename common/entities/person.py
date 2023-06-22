
from common.entities.entity import EntityObject
from common.utils import IDGenerator

class PersonEntity (EntityObject):
    table_name="EntityTable"
    key_field="id"
    partition_value="persons"
    fields=["id", "sms", "email", "aliases", "photos_album"]

    def __init__(self, d):
        super().__init__(d)
