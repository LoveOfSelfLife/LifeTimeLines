import json
from common.entity_object import EntityObject
from common.entities.syncoperation import LatestItemUpdatedTimeTracker
from common.table_store import TableStore
import re
import urllib.parse

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

    def list_items(self, eobj:EntityObject, filter=None, newer_than_cutoff_ts_iso=None):
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
            for r in storage.query(eobj.get_partition_value(), filter=filter, newer_than_cutoff_ts_iso=newer_than_cutoff_ts_iso):
                yield self._loads_from_storage_format(r, type(eobj))
        else:
            for r in storage.query(filter=filter, newer_than_cutoff_ts_iso=newer_than_cutoff_ts_iso):
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
    
    def get_iso_timestamp_of_latest_stored_item(self, eobj):
        return self.get_iso_timestamp_of_latest_stored_item_in_table(eobj.get_table_name())

    def get_iso_timestamp_of_latest_stored_item_in_table(self, table):
        latest = LatestItemUpdatedTimeTracker({"table_name": table})
        rec = self.get_item(latest)
        if rec is None:
            return rec.get("latest_item_updated_iso", None)
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
            self._update_timestamp_of_latest_stored_item(eobj, last_item_meta)
        return 1

    def upsert_items(self, entities, track_last_updated_item=True):
        if hasattr(entities, "__iter__"):
            if len(entities) > 0:
                eobj = entities[0]
                storage = EntityStore._get_storage_by_table_name(eobj.get_table_name())
                _, last_item_meta = storage.batch_upsert([self._dumps_to_storage_format(e) for e in entities])
                if track_last_updated_item:
                    self._update_timestamp_of_latest_stored_item(eobj, last_item_meta)
                return len(entities)
            return 0
        else:
            raise Exception("entities must be a list of EntityObject instances")
    
    def _update_timestamp_of_latest_stored_item(self, eobj, last_item):
        last_item_time_iso = self._get_ts_from_metadata_etag(last_item)
        latest_item_record = LatestItemUpdatedTimeTracker({"table_name": eobj.get_table_name(), "latest_item_updated_iso": last_item_time_iso})
        self.upsert_item(latest_item_record, track_last_updated_item=False)
                
    def _get_ts_from_metadata_etag(self, item):
        # item is a dict like this: {'etag': 'W/"datetime\'2024-03-06T14%3A09%3A41.3067052Z\'"'}
        ts = None
        etag = item.get('etag', None)
        if etag:
            pat = re.compile(r"W/\"datetime'(.*)'\"")
            ts_url_encoded = re.match(pat, etag).group(1)
            
            ts = urllib.parse.unquote(ts_url_encoded)
        return ts


    def delete(self, row_keys, entity_class):
        if entity_class.partition_value is None:
            raise Exception("partition value not defined")
        storage = EntityStore._get_storage_by_table_name(entity_class.table_name)
        for rk in row_keys:
            storage.delete_item(partition_key=entity_class.partition_value, row_key=rk)

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
                vals[k] = json.dumps(v)
        return vals
