from datetime import datetime
from common.entity_store import EntityStore, EntityObject, LatestItemUpdatedTimeTracker
from common.table_store import TableStore

class ConsumedItemsTimeTracker (EntityObject):
    table_name='ConsumedItemsTrackerTable'
    partition_field="consumer_id"
    key_field="table_name"
    fields=["consumer_id", "table_name", "latest_item_consumed_iso"]

    def __init__(self, d={}):
        super().__init__(d)

def get_iso_timestamp_of_latest_stored_item(table_name):
    return get_iso_timestamp_of_latest_stored_item_in_table(table_name)

def get_iso_timestamp_of_latest_stored_item_in_table(table:str):
    es = EntityStore()
    latest = LatestItemUpdatedTimeTracker({"table_name": table})
    rec = es.get_item(latest)
    if rec:
        return rec.get("latest_item_updated_iso", None)
    return None

def get_iso_timestamp_of_last_consumed_entity(table_name:str, consumer_id:str):
    """
    Retrieve timestamp of last consumed entity
    """
    es = EntityStore()
    consumed_rec = es.get_item(ConsumedItemsTimeTracker({"table_name":table_name, "consumer_id":consumer_id}))
    return consumed_rec.get("latest_item_consumed_iso", None) if consumed_rec else None

def set_iso_timestamp_of_last_consumed_entity(table_name:str, consumer_id:str, ts_iso:str):
    """
    set the timestamp of the last consumed entity
    """
    es = EntityStore()
    co = ConsumedItemsTimeTracker({"table_name":table_name, 
                                   "consumer_id":consumer_id, 
                                   "latest_item_consumed_iso": ts_iso})
    es.upsert_item(co)

def any_unconsumed_entities(eobj:EntityObject, consumer_id:str):
    """
    any unconsumed entities for a given consumer
    """
    latest_entity_ts_iso = get_iso_timestamp_of_latest_stored_item(eobj.get_table_name())
    if latest_entity_ts_iso is None:
        return False

    consumed_ts_iso = get_iso_timestamp_of_last_consumed_entity(eobj.get_table_name(), consumer_id)
    if consumed_ts_iso is None:
        return True
    
    if _iso_lessthan(consumed_ts_iso, latest_entity_ts_iso):
        return True
    return False

def _iso_lessthan(iso1:str, iso2:str):
    """
    Compare two ISO formatted timestamps
    """
    dt1 = datetime.fromisoformat(iso1)
    dt2 = datetime.fromisoformat(iso2)
    return dt1 < dt2

def find_serializable_unconsumed_entity_ranges(table_name, consumer_id, range_length):
    result = find_unconsumed_entity_ranges(table_name, consumer_id, range_length)
    
    return [(str(r[0].strftime("%Y-%m-%dT%H:%M:%S.%f")[:] + 'Z' if r[0] else None), str(r[1].strftime("%Y-%m-%dT%H:%M:%S.%f")[:] + 'Z' if r[1] else None)) for r in result]

def find_unconsumed_entity_ranges(table_name, consumer_id, range_length):
    """
    Find unconsumed entity ranges
    """
    latest_entity_ts_iso = get_iso_timestamp_of_latest_stored_item(table_name)
    if latest_entity_ts_iso is None:
        return []

    last_consumed_ts_iso = get_iso_timestamp_of_last_consumed_entity(table_name, consumer_id)

    timestamps_list = _extract_sorted_timestamps_from_entity_table(table_name, start_time_iso=last_consumed_ts_iso, end_time_iso=latest_entity_ts_iso)
    spl = list(_split_list_into_ranges_of_size_num(timestamps_list, range_length))

    return [(timestamps_list[s[0]], timestamps_list[s[1]] if s[1] else None) for s in spl]
    
def _extract_sorted_timestamps_from_entity_table(table_name, start_time_iso, end_time_iso):
    """
    Query timestamps from entity table that fall within a given range from start to end
    """
    # here we choose to use the TableStore directly, instead of the EntityStore, because we only need the timestamps
    tblstore : TableStore = TableStore(table_name)
    ts_list=[]
    for mi in tblstore.query(select=["Timestamp"], 
                             start_time_iso=start_time_iso, 
                             end_time_iso=end_time_iso):
        ts_list.append(mi.metadata["timestamp"])
    ts_list.sort()
    return ts_list

def _find_next_split(p, L, num):
    """
    """
    q = p+num
    while q+1 < len(L) and L[q] == L[q+1]:
        q += 1
    return q

def _split_list_into_ranges_of_size_num(ts_list, num):
    """
    break up a list into smaller chunks, where each chunk is represented as a range with start & end indices, where each chunk has approximately length equal to num
    return an iterator over those ranges 
    this method will only break ts_list at a point N, if ts_list[N-1] is not equalt to ts_list[N], otherwise it will increase N until it finds a different value
    thus, that is why the resulting ranges are approximate, some ranges may be longer than num
    e.g. if we want to break up the list [1,2,3,4,5,6,7] into ranges of size 3, the result will be [(0,3), (3,6)], representing the ranges [1,2,3] and [4,5,6]
    however, if we want to break up the list [1,2,3,3,4,5,5,5,5,6,7] into ranges of size 3, the result will be [(0,4), (4,9), (9,11)], representing the ranges [1,2,3,3], [4,5,5,5,5] and [6,7]
    Note that the end of the first range, 3, is not equal to the start of the second range, 4, so the first range breaks with 4 elements, not 3 elements
    """
    len_L = len(ts_list)
    p = 0
    while p < len_L:
        splits_at = _find_next_split(p, ts_list, num)
        if splits_at < len_L:
            yield (p, splits_at)
        else:
            yield (p, None)
        p = splits_at+1

if __name__ == "__main__":
    pass
