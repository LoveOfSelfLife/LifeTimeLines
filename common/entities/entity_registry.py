
from common.configs import DriveSyncConfig
from common.entities.person import PersonEntity
from common.entities.location import LocationEntity

class EntityRegistry:
    editable_entities = {
        "drivesyncconfig" : DriveSyncConfig(),
        "people" : PersonEntity(),
        "locations" : LocationEntity()
    }
    non_editable_entities = {
    }
    entities = {**editable_entities, **non_editable_entities}

def get_editable_entity_names():
    return list(EntityRegistry.editable_entities.keys())

def get_editable_entity_by_name(name):
    return EntityRegistry.editable_entities.get(name, None)
