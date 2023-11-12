import json
from common.table_store import TableStore

class EntityStore :

    def __init__(self, entity_class):
        self.storage = TableStore(entity_class.table_name)
        self.partition_field = entity_class.partition_field
        self.partition_value = entity_class.partition_value
        self.key_field = entity_class.key_field
        self.fields = entity_class.fields
        self.entity_class = entity_class

    def list_items(self, filter=None):
        for r in self.storage.query(self.partition_value, filter):
            yield self._loads_from_storage_format(r)


    def _get_partition_key(self, e):
        if self.partition_value:
            return self.partition_value
        else:
            return e[self.partition_field]
    
    def _get_row_key(self, e):
        return e[self.key_field]

    def _set_row_key(self, e, v):
        e[self.key_field] = v
    
    # @staticmethod
    def _prep_for_storage(self, e):
        if hasattr(e, 'key_field') and hasattr(e, 'fields'):
            keys = {"PartitionKey": self._get_partition_key(e), "RowKey": self._get_row_key(e)}
            vals = { attr: e[attr] for attr in e.fields}
            return {**keys, **vals}
        else:
            return e
            
    def get_item(self, key):
        results = self.storage.query(self.partition_value, f"RowKey eq '{key}'")
        pl = [self._loads_from_storage_format(p) for p in results]
        if len(pl) > 0:
            return pl[0] 
        else:
            return "notfound", 404

    def upsert_item(self, pe):
        if type(pe) != self.entity_class:
            raise Exception("instance in wrong table")

        if self.key_field not in pe.keys():
            id = (type(pe).key_generator)()
            self._set_row_key(pe, str(id))

        self.storage.upsert(partition_key=self._get_partition_key(pe),
                            row_key=self._get_row_key(pe),
                            vals=self._dumps_to_storage_format(pe))
        return "ok", 201
    
    def upsert_items(self, entities):
        self.storage.batch_upsert([self._prep_for_storage(e) for e in entities])

    def delete(self, row_keys):
        for rk in row_keys:
            self.storage.delete_item(partition_key=self.partition_value, row_key=rk)

    def delete_all(self):
        self.storage.delete(self.partition_value, None)        

    def delete_filtered(self, filter=None):
        self.storage.delete(self.partition_value, filter)

    def _loads_from_storage_format(self, item_in_storage_format):
        base = {}
        base['type'] = self._get_partition_key(item_in_storage_format)
        self._set_row_key(base, item_in_storage_format[ 'RowKey' ])
        # base[ self.key_field ] = item_in_storage_format[ 'RowKey' ]
        for k,v in item_in_storage_format.items():
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
    