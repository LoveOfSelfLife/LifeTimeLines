from datetime import datetime, tzinfo
from common.entities.syncoperation import LatestItemUpdatedTimeTracker, SyncOperation
from common.utils import generate_unique_id
from googlephotosapi import GooglePhotosApi
from common.google_credentials import get_credentials
from common.table_store import TableStore
from common.date_ranges_mgr import add_range, load_date_ranges, get_first_unexplored_date_range, get_unexplored_date_ranges
from common.date_ranges_mgr import break_up_date_range_into_chunks
from common.date_ranges_mgr import coaslesc_ranges
from common.date_ranges_mgr import shift_date_and_round_to_day
from common.entity_store import EntityStore
from common.entities.photos import PhotosDateRanges, MediaItem
from datetimerange import DateTimeRange

MAX_DAYS_TO_GET_PER_REQUEST=100

class PhotosSyncMgr ():
    def __init__(self):
        self.photos_api = GooglePhotosApi(get_credentials())
        self.storage = EntityStore()

    def sync_photos_in_date_range(self, from_dt, to_dt):
        num_mitems_processed = 0
        newly_explored_range = DateTimeRange(from_dt, to_dt)
        mitems = self.photos_api.get_media_items_in_datetime_range(from_dt, to_dt) 

        entities = [ MediaItem({"mitemId": e['id'], 
                                "creationTime": e['creationTime'],
                                "mimeType" : e['mimeType']}) for e in mitems]

        _, last_item_iso = self.storage.upsert_items(entities)
        latest_item_record = LatestItemUpdatedTimeTracker({"table_name": MediaItem.get_table_name(), "latest_item_updated_iso": last_item_iso})
        self.storage.upsert_item(latest_item_record)

        num_mitems_processed += len(entities)

        explored_date_ranges =  load_date_ranges(self.storage.list_items(PhotosDateRanges()))
        
        explored_date_ranges = add_range(newly_explored_range, explored_date_ranges)

        coalesced_date_ranges = coaslesc_ranges(explored_date_ranges)

        self.storage.delete_all_in_partition(PhotosDateRanges, "photos")
        coalesced_ranges_to_store = [PhotosDateRanges({"startDate": str(r.start_datetime),
                                                       "endDate": str(r.end_datetime) }) for r in coalesced_date_ranges]
        self.storage.upsert_items(coalesced_ranges_to_store)

        return { "start_dt": str(from_dt), "end_dt": str(to_dt), "num_items_synced": num_mitems_processed }
    
    def get_unexplored_date_ranges(self, start_range_iso, end_range_iso, max_range_length):
        print('get_unexplored_date_ranges')

        if not max_range_length:
            max_range_length = 30

        extent = self.photos_api.get_media_items_daterange_extent()
        earliest_media_item_iso = extent['earliest']
        latest_media_item_iso  = extent['latest']
        
        if not start_range_iso:
            start_range_iso = earliest_media_item_iso

        if not end_range_iso:
            end_range_iso = latest_media_item_iso

        start_range_dt = datetime.fromisoformat(start_range_iso).replace(tzinfo=None)
        end_range_dt = datetime.fromisoformat(end_range_iso).replace(tzinfo=None)

        explored_date_ranges =  load_date_ranges(self.storage.list_items(PhotosDateRanges()))
        explored_date_ranges =  []
        
        unexplored_date_ranges = get_unexplored_date_ranges(explored_date_ranges,
                                                            earliest_media_item_iso, 
                                                            latest_media_item_iso)
        for unexplored_range in unexplored_date_ranges:
            start_dt = shift_date_and_round_to_day(unexplored_range.start_datetime, -1)
            end_dt = shift_date_and_round_to_day(unexplored_range.end_datetime, 1)

            sub_ranges = break_up_date_range_into_chunks(start_dt,
                                                         end_dt,
                                                         max_range_length)
            for sr in sub_ranges:
                sr:DateTimeRange = sr
                if sr.end_datetime < start_range_dt:
                    continue
                if sr.start_datetime > end_range_dt:
                    continue
                yield { "start" : sr.get_start_time_str(), "end" : sr.get_end_time_str() }

if __name__ == '__main__':
    import os
    from dotenv import load_dotenv
    load_dotenv()
    TableStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))

    psm = PhotosSyncMgr()
    rs =  psm.get_unexplored_date_ranges('20240101', '20240213', 20)
    rsl = list(rs)
    print(rsl)
    psm.sync_photos_in_date_range(datetime.fromisoformat('2024-02-01T00:00:00'), 
                                  datetime.fromisoformat('2024-02-13T00:00:00'))
