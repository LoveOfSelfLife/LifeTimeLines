from datetime import datetime
import json
import re
import urllib
from common.entity_filter import Filter
from common.table_store import TableStore
from common.id_generator import IDGenerator

  
class EntityObject (dict):
    table_name = None
    fields = None
    key_field=None
    partition_field=None
    partition_value=None
    items_list_field = None
    is_editable = False
    schema=None
    entity_name_to_entity_class_map = {}
    display_name = None


    def __init__(self, d={}):
        dict.__init__(d)
        self.initialize(d)
        
    def initialize(self, d={}):
        for k,v in d.items():
            self[k] = v
        self.validate()
        print(f"EntityObject: adding { self.get_table_name() } to entity_name_to_entity_class_map")
        EntityObject.entity_name_to_entity_class_map[self.get_table_name()] = self.__class__
    
    @staticmethod
    def get_entity_class_from_table_name(table_name):
        """Get the entity class from the table name.

        Args:
            cls (type): The class type of the entity.

        Returns:
            type: The entity class corresponding to the table name.
        """
        return EntityObject.entity_name_to_entity_class_map.get(table_name, None)
    
    def get_name(self):
        return type(self).__name__
    
    def get_display_name(self):
        if type(self).display_name:
            return type(self).display_name
        if self.get_table_name().endswith("Table"):
            return self.get_table_name()[:-5]
        else:
            return self.get_table_name()
            
    def set_partition_value(self, partition_value):
        if self.get_static_partition_value():
            print("Cannot set partition value for this entity, it is static")
        self[self.get_partition_field()] = partition_value

    def get_key_field(self):
        return type(self).key_field
    
    def get_key_value(self):
        return self[self.get_key_field()]

    def get_partition_field(self):
        return type(self).partition_field

    def get_partition_value(self):
        if type(self).partition_value:
            return type(self).partition_value
        return self.get(self.get_partition_field(), None)
    
    def get_composite_key(self):
        return (self.get_key_value(), self.get_partition_value(), self.get_table_name())

    def get_static_partition_value(self):
        if type(self).partition_value:
            return type(self).partition_value
        return None

    def get_table_name(self):
        return type(self).table_name

    def get_fields(self):
        return type(self).fields
    
    def get_items_list_field(self):
        return type(self).items_list_field

    def get_schema(self):
        return type(self).schema

    def get_key_generator(self):
        tbl = type(self).table_name
        if len(tbl) > 3:
            tbl3 = tbl[:3]
        else:
            tbl3 = tbl
        return lambda: f"{tbl3}_{IDGenerator.get_unique_id(tbl)}"

    def validate(self):
        return True
            
class LatestItemUpdatedTimeTracker (EntityObject):
    table_name='LatestItemsUpdatedTrackerTable'
    partition_value="all"
    key_field="table_name"
    fields=["table_name", "latest_item_updated_iso", "partition_value"]

    def __init__(self, d={}):
        super().__init__(d)

def update_timestamp_of_latest_stored_item(eobj, last_item):
    es = EntityStore()    
    last_item_time_iso = _get_ts_from_metadata_etag(last_item)
    latest_item_record = LatestItemUpdatedTimeTracker({"table_name": eobj.get_table_name(), "latest_item_updated_iso": last_item_time_iso, "partition_value": eobj.get_partition_value()})
    es.upsert_item(latest_item_record, track_last_updated_item=False)
            
def _get_ts_from_metadata_etag(item):
    # item is a dict like this: {'etag': 'W/"datetime\'2024-03-06T14%3A09%3A41.3067052Z\'"'}
    ts = None
    etag = item.get('etag', None)
    if etag:
        pat = re.compile(r"W/\"datetime'(.*)'\"")
        ts_url_encoded = re.match(pat, etag).group(1)
        
        ts = urllib.parse.unquote(ts_url_encoded)
        
    return ts

def instatiate_all_entity_objects():
    for cls in recursive_subclasses(EntityObject):
        cls()

def recursive_subclasses(klass):
    """Yield all subclasses of the given class, recursively."""
    seen = set()
    for subclass in klass.__subclasses__():
        yield subclass
        for subsubclass in recursive_subclasses(subclass):
            if subsubclass not in seen:
                seen.add(subsubclass)
                yield subsubclass

class EntityStore :
    storage_map = {}

    def __init__(self):
        pass

    @staticmethod
    def _get_storage_by_table_name(table_name):
        storage = EntityStore.storage_map.get(table_name, None)
        if not storage:
            storage = TableStore(table_name)
            EntityStore.storage_map[table_name] = storage
        return storage

    def list_items(self, eobj:EntityObject, filter=None, dfilter=None, select=None, start_time_iso=None, end_time_iso=None,
                   include_start_time=False, include_end_time=True):
        """return a iterator of objects from the underlying Table store

        Args:
            entity_class (EntityObject instance): used to determine the table name that this method will query
            filter (string, optional): used to filter the results to only include items that satisfy the filter. Defaults to None.
            newer_than_cutoff_ts_iso (ios formatter string, optional): used to return only those items that were updated in the table after the cutoff time. Defaults to None.
        Yields:
            EntityObject : an iterator of entity objects of the desiried type
        """
        # if entity_class has a value for the "items_list_field" attribute, then any entity
        # may possily be spread out across multiple Table storage rows.   In that case, we only 
        # want to retrieve the base entity objects, which can be identified as have a Null value
        # in the underlying row's _Parent attribute.  To make sure this occurs, we add a filter

        storage = EntityStore._get_storage_by_table_name(eobj.get_table_name())
        if eobj.get_items_list_field() is not None:
            pass
            # filter = filter
            # TODO: complete this
        if eobj.get_static_partition_value():
            for r in storage.query(eobj.get_partition_value(), filter=filter, dfilter=dfilter, select=select, 
                                   start_time_iso=start_time_iso, 
                                   end_time_iso=end_time_iso,
                                   include_start_time=include_start_time, 
                                   include_end_time=include_end_time):
                yield self._loads_from_storage_format(r, type(eobj))
        else:
            for r in storage.query(eobj.get_partition_value(), filter=filter, dfilter=dfilter, select=select, 
                                   start_time_iso=start_time_iso, 
                                   end_time_iso=end_time_iso,
                                   include_start_time=include_start_time, 
                                   include_end_time=include_end_time):
                yield self._loads_from_storage_format(r, type(eobj))

    def list_items2(self, eobj:EntityObject, dfilter=[], select=None, start_time_iso=None, end_time_iso=None,
                   include_start_time=False, include_end_time=True):
        """return a iterator of objects from the underlying Table store

        Args:
            entity_class (EntityObject instance): used to determine the table name that this method will query
            filter (string, optional): used to filter the results to only include items that satisfy the filter. Defaults to None.
            newer_than_cutoff_ts_iso (ios formatter string, optional): used to return only those items that were updated in the table after the cutoff time. Defaults to None.
        Yields:
            EntityObject : an iterator of entity objects of the desiried type
        """
        # if entity_class has a value for the "items_list_field" attribute, then any entity
        # may possily be spread out across multiple Table storage rows.   In that case, we only 
        # want to retrieve the base entity objects, which can be identified as have a Null value
        # in the underlying row's _Parent attribute.  To make sure this occurs, we add a filter

        storage = EntityStore._get_storage_by_table_name(eobj.get_table_name())
        if eobj.get_items_list_field() is not None:
            pass
            # filter = filter
            # TODO: complete this
        if eobj.get_partition_value():
            dfilter.append(Filter("PartitionKey", eobj.get_partition_value(), op="eq"))

        for r in storage.query2(dfilter=dfilter, select=select, 
                                start_time_iso=start_time_iso, 
                                end_time_iso=end_time_iso,
                                include_start_time=include_start_time, 
                                include_end_time=include_end_time):
            yield self._loads_from_storage_format(r, type(eobj))

    def get_item(self, eobj):
        try:
            storage = EntityStore._get_storage_by_table_name(eobj.get_table_name())
            base_item = storage.get_item(partition_key_value=eobj.get_partition_value(), 
                                    row_key_value=eobj.get_key_value())
            if eobj.get_items_list_field() is not None:
                # TODO: this whole block is untested, it is also just a draft
                additonal_list_items = []
                next_id = base_item.get("_Next", None)
                while next_id:
                    next_item = storage.get_item(partition_key_value=eobj.get_partition_value(), 
                                            row_key_value=next_id)
                    additonal_list_items.append(next_item[eobj.get_items_list_field()])
                    next_id = next_item.get("_Next", None)
                base_item[eobj.get_items_list_field()] = list(base_item[eobj.get_items_list_field()]) + additonal_list_items

            return self._loads_from_storage_format(base_item, type(eobj))
        except Exception:
            return None
        
    def get_item_by_composite_key(self, eobj, composite_key):
        (key, partition) = composite_key
        return self.get_item_by_key(eobj, key, partition)
    
    def get_item_by_composite_key2(self, composite_key):
        (key, partition, entity_name) = tuple(composite_key)
        # eobj = EntityObject.get_entity_class_from_table_name(entity_name)()
        eobj = EntityObject.get_entity_class_from_table_name(entity_name)()
        return self.get_item_by_key(eobj, key, partition)    
    
    def get_item_by_key(self, eobj, key_value, partition_value=None):
        try:
            storage = EntityStore._get_storage_by_table_name(eobj.get_table_name())
            base_item = storage.get_item(partition_key_value=partition_value if partition_value else eobj.get_partition_value(),
                                    row_key_value=key_value)
            kf = eobj.get_key_field()
            pf = eobj.get_partition_field()
            eobj[kf] = key_value
            if pf and partition_value:
                eobj[pf] = partition_value

            if eobj.get_items_list_field() is not None:
                # TODO: this whole block is untested, it is also just a draft
                additonal_list_items = []
                next_id = base_item.get("_Next", None)
                while next_id:
                    next_item = storage.get_item(partition_key_value=eobj.get_partition_value(), 
                                            row_key_value=next_id)
                    additonal_list_items.append(next_item[eobj.get_items_list_field()])
                    next_id = next_item.get("_Next", None)
                base_item[eobj.get_items_list_field()] = list(base_item[eobj.get_items_list_field()]) + additonal_list_items

            return self._loads_from_storage_format(base_item, type(eobj))
        except Exception:
            return None
    def upsert_item(self, eobj, track_last_updated_item=True):
        storage = EntityStore._get_storage_by_table_name(eobj.get_table_name())
        if eobj.get_key_field() not in eobj.keys():
            id = (eobj.get_key_generator())()
            eobj[eobj.get_key_field()] = str(id)
        last_item_meta = storage.upsert(partition_key=eobj.get_partition_value(),
                                        row_key=eobj.get_key_value(),
                                        vals=self._dumps_to_storage_format(eobj))
        if track_last_updated_item:
            update_timestamp_of_latest_stored_item(eobj, last_item_meta)
        return 1

    def upsert_items(self, entities, track_last_updated_item=True):
        if hasattr(entities, "__iter__"):
            if len(entities) > 0:
                eobj = entities[0]
                storage = EntityStore._get_storage_by_table_name(eobj.get_table_name())
                _, last_item_meta = storage.batch_upsert([self._dumps_to_storage_format(e) for e in entities])
                if track_last_updated_item and last_item_meta:
                    update_timestamp_of_latest_stored_item(eobj, last_item_meta)
                return len(entities)
            return 0
        else:
            raise Exception("entities must be a list of EntityObject instances")

    def delete(self, row_keys, entity_class):
        if entity_class.partition_value is None:
            raise Exception("partition value not defined")
        storage = EntityStore._get_storage_by_table_name(entity_class.table_name)
        for rk in row_keys:
            storage.delete_item(partition_key=entity_class.partition_value, row_key=rk)

    def delete_items(self, items_list):
        for item in items_list:
            if item.get_partition_value() is None:
                raise Exception("partition value not defined")
            storage = EntityStore._get_storage_by_table_name(item.get_table_name())
            storage.delete_item(partition_key=item.get_partition_value(), row_key=item.get_key_value())

    def delete_all_in_partition(self, entity_class, partition_value):
        storage = EntityStore._get_storage_by_table_name(entity_class.table_name)
        storage.delete(partition_value, None)  


    def delete_all(self, entity_class):
        storage = EntityStore._get_storage_by_table_name(entity_class.table_name)
        storage.delete_all()
    
    def _set_partition_key(self, cls, e, v):
        if cls.partition_field:
            e[cls.partition_field] = v

    def _get_row_key(self, e):
        return e[e.get_key_field()]

    def _set_row_key(self, cls, e, v):
        e[cls.key_field] = v
    
    def _loads_from_storage_format(self, item_in_storage_format, item_class):
        base = {}
        self._set_row_key(item_class, base, item_in_storage_format[ 'RowKey' ])
        self._set_partition_key(item_class, base, item_in_storage_format[ 'PartitionKey' ])
        base['Timestamp'] = str(item_in_storage_format.metadata['timestamp'])

        for k,v in item_in_storage_format.items():
            if k in item_class.fields:
                try:
                    base[k] = json.loads(v)
                except json.JSONDecodeError:
                    base[k] = v

        eobj = (item_class)(base)
        return eobj

    def _dumps_to_storage_format(self, eobj):
        vals = {}
        vals["PartitionKey"] = eobj.get_partition_value()
        vals["RowKey"] = eobj.get_key_value()
        for k,v in eobj.items():
            if k in eobj.get_fields() and k != eobj.get_partition_field() and k != eobj.get_key_field():
                vals[k] = json.dumps(v) if type(v) is not str else v  # don't double encode strings, otherwise they will have extra quotes
        return vals
