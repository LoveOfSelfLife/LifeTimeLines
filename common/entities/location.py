from common.entity_store import EntityObject

class LocationEntity (EntityObject):
    table_name="EntityTable"
    key_field="id"
    partition_value="locations"
    fields=["id", "aliases", "name", "city"]

    def __init__(self, d={}):
        super().__init__(d)
