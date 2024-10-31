
import os
from dotenv import load_dotenv
import unittest
import datetime
from datetime import timedelta 
import time
import json
from common.entities.photos import MediaItem
from common.entities.location import LocationEntity
from common.entities.person import GenericEntity, PersonEntity
from common.entity_consumer import ConsumedItemsTimeTracker, find_unconsumed_entity_ranges
from common.entity_consumer import set_iso_timestamp_of_last_consumed_entity
from common.entity_store import EntityStore
from common.table_store import TableStore

from common.entity_store import EntityObject
from test_consumption import add_microseconds

# def add_microseconds(ts, ms=1):
#     ts0 = (datetime.datetime.fromisoformat(str(ts))  + timedelta(microseconds=ms)) if ts else None
#     ts1 = ts0.strftime("%Y-%m-%dT%H:%M:%S.%f")[:] + 'Z' if ts0 else None
#     return ts1

MEDIA_ITEM_CONSUMER_ID = "mediaitem_consumer_process"
class TestMediaItemConsumers(unittest.TestCase):

    def setUp(self) -> None:
        print(f"setUp()")
        load_dotenv('test/.env')
        print(f"{os.getcwd()}")
        TableStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))

        storage = EntityStore()
        storage.delete_all_in_partition(ConsumedItemsTimeTracker(), partition_value=MEDIA_ITEM_CONSUMER_ID)

        return super().setUp()
    
    def test_populateC2(self):
        print(f"populateC2")
        storage = EntityStore()
        ctr = 0
        rngs = find_unconsumed_entity_ranges(MediaItem(), MEDIA_ITEM_CONSUMER_ID, 1500)
        print(f"number of ranges: {len(rngs)}")
        if rngs:
            for r in rngs:
                (s,e) = r
                print(f"********** process range: ({s},{e}) \n {r}")
                ctr = 0
                items = storage.list_items(MediaItem(), 
                                            start_time_iso=add_microseconds(s,-1), 
                                            end_time_iso=e, 
                                            include_start_time=True)
                for i in items:
                    mr = datetime.datetime.fromisoformat(str(i["Timestamp"]))
                    ctr += 1
                    if ctr < 3:
                        print(f"item: {i}")
            
                max_timestamp_iso = mr.strftime("%Y-%m-%dT%H:%M:%S.%f")[:] + 'Z'
                set_iso_timestamp_of_last_consumed_entity(MediaItem().get_table_name(), MEDIA_ITEM_CONSUMER_ID, max_timestamp_iso)
            
if __name__ == '__main__':
    unittest.main()
