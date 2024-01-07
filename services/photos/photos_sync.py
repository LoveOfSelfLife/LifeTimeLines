from common.entities.syncoperation import SyncOperation
from common.utils import generate_unique_id
from googlephotosapi import GooglePhotosApi
from common.google_credentials import get_credentials
from common.table_store import TableStore
from common.date_ranges_mgr import add_range, load_date_ranges, get_first_unexplored_date_range
from common.date_ranges_mgr import break_up_date_range_into_chunks
from common.date_ranges_mgr import coaslesc_ranges
from common.entity_store import EntityStore
from common.entities.photos import PhotosDateRanges, MediaItem

MAX_DAYS_TO_GET_PER_REQUEST=100

class PhotosSyncMgr ():
    def __init__(self):
        self.api = GooglePhotosApi(get_credentials())
        self.media_items_tbl = EntityStore(MediaItem)
        self.date_ranges_tbl = EntityStore(PhotosDateRanges)

    def execute_photos_sync(self, max_days_to_process=0):
        print('start photos synchronization')

        # find a range of dates that have not yet been pulled down from photos
        # use api to retrieve those photos, collect into a list
        # insert list into media items table in a batch operation
        # add the date range to the set of explored date ranges
        # repeat until there are no more unexplored range

        num_days_processed = 0
        num_mitems_processed = 0 

        extent = self.api.get_media_items_daterange_extent()
        earliest_media_item_iso = extent['earliest']
        latest_media_item_iso  = extent['latest']
        
        explored_date_ranges =  load_date_ranges(self.date_ranges_tbl.list_items())
        
        unexplored_date_range = get_first_unexplored_date_range(explored_date_ranges,
                                                                earliest_media_item_iso, 
                                                                latest_media_item_iso)
        while unexplored_date_range:
            sub_ranges = break_up_date_range_into_chunks(unexplored_date_range.start_datetime, 
                                                         unexplored_date_range.end_datetime,
                                                         MAX_DAYS_TO_GET_PER_REQUEST)

            for range_to_explore in sub_ranges:
                from_dt = range_to_explore.start_datetime
                to_dt = range_to_explore.end_datetime
                mitems = self.api.get_media_items_in_datetime_range(from_dt, to_dt) 

                entities = [ MediaItem({"mitemId": e['id'], 
                                        "creationTime": e['creationTime'],
                                        "mimeType" : e['mimeType']}) for e in mitems]

                self.media_items_tbl.upsert_items(entities)
                num_mitems_processed += len(entities)
                explored_date_ranges = add_range(range_to_explore, explored_date_ranges)

                num_days_processed += range_to_explore.timedelta.days

                if max_days_to_process and num_days_processed > max_days_to_process:
                    break

            if max_days_to_process and num_days_processed > max_days_to_process:
                break

            unexplored_date_range = get_first_unexplored_date_range(explored_date_ranges,
                                                              earliest_media_item_iso, latest_media_item_iso)            

        coalesced_date_ranges = coaslesc_ranges(explored_date_ranges)

        self.date_ranges_tbl.delete_all_in_partition("photos")
        coalesced_ranges_to_store = [PhotosDateRanges({"startDate": str(r.start_datetime),
                                                       "endDate": str(r.end_datetime) }) for r in coalesced_date_ranges]
        self.date_ranges_tbl.upsert_items(coalesced_ranges_to_store)

        is_done = False if unexplored_date_range else True
        return is_done, num_mitems_processed, num_days_processed


if __name__ == '__main__':
    import os
    from dotenv import load_dotenv
    load_dotenv()
    TableStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))

    es = EntityStore(PhotosDateRanges)
    ranges = load_date_ranges(es.list_items())
    print(ranges)
    is_done = False
    
    while not is_done:
        psm = PhotosSyncMgr()
        is_done, num_mitems_processed, num_days_processed = psm.execute_photos_sync(365)
        print(f"is done: {is_done}, nitems: {num_mitems_processed}, ndays: {num_days_processed}")

