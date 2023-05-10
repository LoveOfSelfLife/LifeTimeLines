from common.utils import generate_unique_id
from googlephotosapi import GooglePhotosApi
from common.google_credentials import get_credentials
from common.tables import EntityStore
from common.date_ranges_mgr import add_range, load_date_ranges_from_storage, get_unexplored_date_range, save_date_ranges_to_storage
from common.date_ranges_mgr import break_up_date_range_into_chunks
from common.date_ranges_mgr import coaslesc_ranges

SYNC_OPS_TBL = 'SyncOperationTable'
MEDIA_ITEMS_TBL = 'MediaItemsTable'
DATE_RANGES_TBL = "DateRangesTable"
ALBUM_LAST_ITEM_SYNCED_TBL = "AlbumLastItemSyncedTable"
MAX_DAYS_TO_GET_PER_REQUEST=30

class PhotosSyncMgr ():
    def __init__(self):
        self.api = GooglePhotosApi(get_credentials())
        pass

    def list_operations(self):
        sync_tbl = EntityStore(SYNC_OPS_TBL)
        results = sync_tbl.query('photos')
        return list(results)

    def create_sync_operation(self, **operation_detail):
        # create new unique task for the operation
        # record the task along with the details
        sync_tbl = EntityStore(SYNC_OPS_TBL)
        id = generate_unique_id(SYNC_OPS_TBL)
        sync_tbl.insert(id, 'photos', {"status" : "init"})
        # start processing a small the task
        return { "operationid" : id }

    def get_operation(self, id):
        sync_tbl = EntityStore(SYNC_OPS_TBL)
        result = sync_tbl.query("photos", f"RowKey eq '{id}'")
        item = next(result)
        if item:
            return item
        else:
            return None

    def del_operation(self, id):
        sync_tbl = EntityStore(SYNC_OPS_TBL)
        sync_tbl.delete("photos", f"RowKey eq '{id}'")
        return f'{id}', 204

    def update_operation(self, id, instr):
        sync_tbl = EntityStore(SYNC_OPS_TBL)
        # num = psync.fetch_photos(id)
        # print(f'photos_api_ns.payload: {photos_api_ns.payload}')
        op = self.get_operation(id)
        if op['status'] == "init":
            sync_tbl.upsert(id, 'photos', {"status" : "processing"})
            is_done, num_mitems, num_iterations = self.execute_photos_sync(id)
            ops_tbl = EntityStore(SYNC_OPS_TBL)
            if is_done:
                ops_tbl.upsert(id, 'photos', {"status" : "finished"})
            else:
                ops_tbl.upsert(id, 'photos', {"num_items_processed" : num_mitems })
        return f'{"num_items_processed" : {num_mitems}, "status": {"finished" if is_done else "processing"} })', 204


    def _convert_mitems_to_entities(self, mitems):
        return [ {"RowKey": e['id'], "PartitionKey": "media_item", "creationTime": e['creationTime']} for e in mitems]

    def execute_photos_sync(self, id, max_days_to_process=0):
        print('start photos synchronization')

        # find a range of dates that have not yet been pulled down from photos
        # use api to retrieve those photos, collect into a list
        # insert list into media items table in a batch operation
        # add the date range to the set of explored date ranges
        # repeat until there are no more unexplored range

        num_days_processed = 0
        num_mitems_processed = 0 
        earliest_media_item_dt, latest_media_item_dt = self.api.get_media_items_daterange()
        explored_date_ranges =  load_date_ranges_from_storage("photos", EntityStore(DATE_RANGES_TBL))
        media_items_tbl = EntityStore(MEDIA_ITEMS_TBL)
        unexplored_date_range = get_unexplored_date_range(explored_date_ranges,
                                                          earliest_media_item_dt, latest_media_item_dt)
        while unexplored_date_range:
            sub_ranges = break_up_date_range_into_chunks(unexplored_date_range.start_datetime, 
                                                            unexplored_date_range.end_datetime,
                                                            MAX_DAYS_TO_GET_PER_REQUEST)
            for range_to_explore in sub_ranges:
                from_dt = range_to_explore.start_datetime
                to_dt = range_to_explore.end_datetime
                mitems = self.api.get_media_items_in_datetime_range(from_dt, to_dt) 

                entities = self._convert_mitems_to_entities(mitems)
                media_items_tbl.batch_insert(entities)
                num_mitems_processed += len(entities)
                explored_date_ranges = add_range(range_to_explore, explored_date_ranges)
                # explored_date_ranges.append(range_to_explore)
                num_days_processed += range_to_explore.timedelta.days

                if max_days_to_process and num_days_processed > max_days_to_process:
                    break

            if max_days_to_process and num_days_processed > max_days_to_process:
                break

            unexplored_date_range = get_unexplored_date_range(explored_date_ranges,
                                                              earliest_media_item_dt, latest_media_item_dt)            

        coalesced_date_ranges = coaslesc_ranges(explored_date_ranges)
        save_date_ranges_to_storage("photos", coalesced_date_ranges, EntityStore(DATE_RANGES_TBL))

        is_done = False if unexplored_date_range else True
        return is_done, num_mitems_processed, num_days_processed



if __name__ == '__main__':
    import os
    from dotenv import load_dotenv
    load_dotenv()
    EntityStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))

    es = EntityStore("DateRangesTable")
    ranges = load_date_ranges_from_storage('photos', es)
    print(ranges)

    psm = PhotosSyncMgr()
    psm.execute_photos_sync(1)
    