from dataclasses import dataclass, asdict
import json
from common.tables import EntityStore
from common.utils import IDGenerator

"""
from the API, 
CREATE:  to create an entity, caller will pass in a json object representing an entity
expectation is that the json will be deserialized into an Entity object, and then the 
entity object will be persisted in Table storage by calling EntityStore.upsert_item() 

GET Entities list:   to get entities, caller of API (may pass in filter) and will invoke GET method
which will in turn call EntityStore.get_list() to which will return a list of PersonEntity objects
which will be serilized back to the API result as a json list.
Since PersonEntity inherits from dict(), it will serialize naturally

An entity can be represented as a JSON string
the json string can be turned into a Dict, via the loads() method
the entity object, which is a dict, will be a subclass PeronEntity
when we want to persist the PersonEntity object, it has to:
 1. be turned into a flat structure where the values of the top level attributes are strings
 2. need to insure that RowKey and PartitionKey are set

JSON from API -> PeopleEntity (Dict)
PeopleEntity (Dict) -> flattened object to store in table storage -> Table Storage
Table Storage -> flattened object -> PeopleEntity (Dict)

when does the entity ID get created?
When a personEntity is created for the very first time, the ID is created at that time before it 
is stored in table storage

when a person entity is retrieved, the ID comes back at the RowKey
If a person entity is retrieved, and then it is updated and stored, then the ID used will be the original
so it wil act as an upsert

prior to storage, an instance of PersonEntity can be created without an ID.
The ID is generated and assigned when the object is stored.

RowKey and PartitionKey are hidden
RowKey maps to something on the object that is identified as the key
PartitionKey maps to some string that captures the type of entity

{ 
    "sms" : ["9084996994", "8628128351"],
    "email" : ["richkempinski@gmail"],
    "aliases" : ["Rich", "RichK", "Rich Kempinski"],
    "type" : "person"
}

When this is posted to create a new entity,  the ID is not provided so it will generate a new "ID"
the generated "ID" is mapped to "RowKey"
"type" will be mapped to "PartitionKey"
The values of each of the other attributes will be converted to json strings
Then the ojbect will be store in table storage

when the table storage is queried, it will return a rsult that looks like:

{ 
    "sms" : '["9084996994", "8628128351"]',
    "email" : '["richkempinski@gmail"]',
    "aliases" : '["Rich", "RichK", "Rich Kempinski"]',
    "PartitionKey" : "person",
    "RowKey" : "23423423"
}

This object is then converted into a dict by:
1. convert the attribute strings to objects
   e.g. '["9084996994", "8628128351"]' to a list ["9084996994", "8628128351"]
2. "RowKey" maps to "id"
3. "PartitonKey" to "type"


POST requests are not just for create.   If ID is provided, then it will not create but instead update.
POST is more like an upsert.

When defining the entity, need to specify the name of the attribute that will treated as the unique ID
The ID is mapped to the RowKey
There may be composite key

The JSON representation of an entity will have id & type
The object representatio of an entity will be a dict, with "id" and "type" attributes

"""
ENTITY_TBL="EntityTable"
class PersonEntity (dict) :
    config = {
        "key" : "id",
        "partition" : "persons",
        "mappings" : ["sms", "email", "aliases", "photos_album"]
    }

    @staticmethod
    def loads_from_storage_format(storage_format):
        base = {}
        base['type'] = PersonEntity.config["partition"]
        base[ PersonEntity.config["key"] ] = storage_format[ 'RowKey' ]
        for k,v in storage_format.items():
            if k in PersonEntity.config["mappings"]:
                base[k] = json.loads(v)
        pe = PersonEntity(base)
        return pe

    def __init__(self, d):
        dict.__init__(d)
        for k,v in d.items():
            self[k] = v

    def set_id(self, id):
            self[ PersonEntity.config['key']] = str(id)

    def get_row_key(self):
        return self[ PersonEntity.config['key']]

    def get_partition_key(self):
        return PersonEntity.config['partition']

    def dumps_to_storage_format(self):
        vals = {}
        for k,v in self.items():
            if k in PersonEntity.config["mappings"]:
                vals[k] = json.dumps(v)
        return vals            

class PersonEntityStore :

    def __init__(self):
        self.storage = EntityStore(ENTITY_TBL)

    def get_list(self):
        persons = self.storage.query("persons")
        return [PersonEntity.loads_from_storage_format(p) for p in persons]

    def get_item(self, key):
        person = self.storage.query("persons", f"RowKey eq '{key}'")
        pl = [PersonEntity.loads_from_storage_format(p) for p in person]
        if len(pl) > 0:
            return pl[0] 
        else:
            return "notfound", 404

    def upsert_item(self, pe:PersonEntity):
        if PersonEntity.config['key'] not in pe.items():
            id = IDGenerator.gen_id()
            pe.set_id(id)            
        self.storage.upsert(RowKey=pe.get_row_key(), 
                            PartitionKey=pe.get_partition_key(), 
                            vals=pe.dumps_to_storage_format())
        return "ok", 201

    def delete(self, items):
        pass

    def upsert_list(self, items):
        pass

