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
        # TODO: do some validation to check that the fields do not include "RowKey" "PartitionKey" or "Timestamp"

    def list_items(self, filter=None):
        for r in self.storage.query(self.partition_value, filter):
            yield self._loads_from_storage_format(r)

    def get_item(self, eobj):
        if type(eobj) != self.entity_class:
            raise Exception("entity class mismatch from EntityStore")
        
        item = self.storage.get_item(partition_key_value=eobj.get_partition_value(), 
                                     row_key_value=eobj.get_key_value())
        return self._loads_from_storage_format(item)
    
    def upsert_item(self, eobj):
        if type(eobj) != self.entity_class:
            raise Exception("entity object instance mismatch with table storage")

        if self.key_field not in eobj.keys():
            id = (type(eobj).key_generator)()
            self._set_row_key(eobj, str(id))

        self.storage.upsert(partition_key=self._get_partition_key(eobj),
                            row_key=self._get_row_key(eobj),
                            vals=self._dumps_to_storage_format(eobj))
        return "ok", 201
    
    def upsert_items(self, entities):
        self.storage.batch_upsert([self._dumps_to_storage_format(e) for e in entities])

    def delete(self, row_keys):
        if self.partition_value is None:
            raise Exception("partition value not defined")
        for rk in row_keys:
            self.storage.delete_item(partition_key=self.partition_value, row_key=rk)

    def delete_all_in_partition(self, partition_value):
        self.storage.delete(partition_value, None)  

    def delete_all(self):
        self.storage.delete_all()

    def _get_partition_key(self, e):
        if self.partition_value:
            return self.partition_value
        else:
            return e[self.partition_field]
    
    def _set_partition_key(self, e, v):
        if self.partition_field:
            e[self.partition_field] = v

    def _get_row_key(self, e):
        return e[self.key_field]

    def _set_row_key(self, e, v):
        e[self.key_field] = v
    
    def _loads_from_storage_format(self, item_in_storage_format):
        base = {}
        self._set_row_key(base, item_in_storage_format[ 'RowKey' ])
        self._set_partition_key(base, item_in_storage_format[ 'PartitionKey' ])
        base['Timestamp'] = str(item_in_storage_format.metadata['timestamp'])

        for k,v in item_in_storage_format.items():
            if k in self.fields:
                try:
                    base[k] = json.loads(v)
                except json.JSONDecodeError:
                    base[k] = v

        eobj = (self.entity_class)(base)
        return eobj

    def _dumps_to_storage_format(self, eobj):
        vals = {}
        vals["PartitionKey"] = eobj.get_partition_value()
        vals["RowKey"] = eobj.get_key_value()
        for k,v in eobj.items():
            if k in self.fields and k != self.partition_field and k != self.key_field:
                vals[k] = json.dumps(v)
        return vals
