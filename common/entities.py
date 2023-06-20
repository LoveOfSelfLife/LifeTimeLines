import json
from common.tables import TableStore
from common.utils import IDGenerator

class EntityObject (dict):
    key_generator=IDGenerator.gen_id()

    def __init__(self, d):
        dict.__init__(d)
        for k,v in d.items():
            self[k] = v

class EntityStore :

    def __init__(self, entity_class):
        self.storage = TableStore(entity_class.table_name)
        self.partition = entity_class.partition
        self.key = entity_class.key
        self.fields = entity_class.fields
        self.entity_class = entity_class

    def list_items(self):
        for r in self.storage.query(self.partition):
            yield self._loads_from_storage_format(r)

    @staticmethod
    def _prep_for_storage(e):
        if hasattr(e, 'key') and hasattr(e, 'fields') and hasattr(e, 'partition'):
            keys = {"PartitionKey": e.partition, "RowKey": e[e.key]}
            vals = { key: e[key] for key in e.fields}
            return {**keys, **vals}
        else:
            return e
            
    def get_item(self, key):
        results = self.storage.query(self.partition, f"RowKey eq '{key}'")
        pl = [self._loads_from_storage_format(p) for p in results]
        if len(pl) > 0:
            return pl[0] 
        else:
            return "notfound", 404

    def upsert_item(self, pe):
        if type(pe) != self.entity_class:
            raise Exception("instance in wrong table")

        if self.key not in pe.keys():
            id = (type(pe).key_generator)()
            pe[self.key] = str(id)

        self.storage.upsert(partition_key=self.partition,
                            row_key=pe[self.key],
                            vals=self._dumps_to_storage_format(pe))
        return "ok", 201
    
    def upsert_items(self, entities):
        self.storage.batch_upsert([EntityStore._prep_for_storage(e) for e in entities])

    def delete(self, row_keys):
        for rk in row_keys:
            self.storage.delete_item(partition_key=self.partition, row_key=rk)

    def delete_all(self):
        self.storage.delete(self.partition, None)        

    def delete_filtered(self, filter=None):
        self.storage.delete(self.partition, filter)

    def _loads_from_storage_format(self, storage_format):
        base = {}
        base['type'] = self.partition
        base[ self.key ] = storage_format[ 'RowKey' ]
        for k,v in storage_format.items():
            if k in self.fields:
                try:
                    base[k] = json.loads(v)
                except json.JSONDecodeError:
                    base[k] = v
        e = (self.entity_class)(base)
        return e

    def _dumps_to_storage_format(self, e):
        vals = {}
        for k,v in e.items():
            if k in self.fields:
                vals[k] = json.dumps(v)
        return vals
    