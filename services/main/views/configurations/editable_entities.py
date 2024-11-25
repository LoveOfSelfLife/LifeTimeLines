
from common.configs import DriveSyncConfig
from common.entities.location import LocationEntity
from common.entities.person import PersonEntity

editable_entities = {
        "divesynccfg" : DriveSyncConfig(),
        "people" : PersonEntity(),
        "locations" : LocationEntity()
    }

def get_editable_entity_names():
    return list(editable_entities.keys())

def get_editable_entity_by_name(name):
    return editable_entities.get(name, None)
