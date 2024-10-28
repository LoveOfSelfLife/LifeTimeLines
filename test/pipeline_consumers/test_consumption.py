
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

class C1Entity (EntityObject):
    table_name="C1Table"
    key_field="id"
    partition_value="nothing"
    fields=["id", "name", "comment"]
    def __init__(self, d={}):
        super().__init__(d)

class C2Entity (EntityObject):
    table_name="C2Table"
    key_field="id"
    partition_value="nothing"
    fields=["id", "name", "comment"]

    def __init__(self, d={}):
        super().__init__(d)

class C3Entity (EntityObject):
    table_name="C3Table"
    key_field="id"
    partition_value="nothing"
    fields=["id", "name", "comment"]

    def __init__(self, d={}):
        super().__init__(d)

def add_microseconds(ts, ms=1):


    ts0 = (datetime.datetime.fromisoformat(str(ts))  + timedelta(microseconds=ms)) if ts else None
    ts1 = ts0.strftime("%Y-%m-%dT%H:%M:%S.%f")[:] + 'Z' if ts0 else None
    return ts1

class TestConsumers(unittest.TestCase):

    def setUp(self) -> None:
        print(f"setUp()")
        load_dotenv('test/.env')
        print(f"{os.getcwd()}")
        print( f"{os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING')}")
        TableStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))

        storage = EntityStore()
        storage.delete_all_in_partition(C1Entity(), partition_value="nothing")
        storage.delete_all_in_partition(ConsumedItemsTimeTracker(), partition_value="process1")
        storage.delete_all_in_partition(ConsumedItemsTimeTracker(), partition_value="process2")
        clist = []
        ctr = 0
        for i in range(10):
            for j in range(3):
                c = C1Entity({"id": f"{ctr}", "name": f"Name{ctr}", "comment": f"Comment{ctr}"})
                clist.append(c)
                ctr += 1
            storage.upsert_items(clist)
            clist = []
            time.sleep(1)

        retrieved_items = storage.list_items(C1Entity())
        for r in retrieved_items:
            print(f"retrieved: {r}")

        return super().setUp()
    
    def test_populateC2(self):
        print(f"populateC2")
        storage = EntityStore()
        print('doing this again for process2 *************************')
        rngs = find_unconsumed_entity_ranges(C1Entity(), "process2", 3)
        print(rngs)
        if rngs:
            for r in rngs:
                (s,e) = r
                print(f"********** process range: ({s},{e}) \n {r}")
                items = storage.list_items(C1Entity(), 
                                            start_time_iso=add_microseconds(s,-1), 
                                            end_time_iso=e, 
                                            include_start_time=True)
                for i in items:
                    print(f"item: {i}")
                    mr = datetime.datetime.fromisoformat(str(i["Timestamp"]))
            
                max_timestamp_iso = mr.strftime("%Y-%m-%dT%H:%M:%S.%f")[:] + 'Z'
                set_iso_timestamp_of_last_consumed_entity(C1Entity().get_table_name(), "process2", max_timestamp_iso)

    def test_populateC1(self):
        print(f"populateC1")
        storage = EntityStore()

        done = False
        while not done:
            rngs = find_unconsumed_entity_ranges(C1Entity(), "process1", 3)
            print(rngs)

            dtlist = []
            if rngs:
                for r in rngs:
                    print(f"********** process first range: {r}")
                    items = storage.list_items(C1Entity(), 
                                               start_time_iso=add_microseconds(r[0],-1), 
                                               end_time_iso=r[1], 
                                               include_start_time=True)
                    for i in items:
                        print(f"item: {i}")
                        dtlist.append(datetime.datetime.fromisoformat(str(i["Timestamp"])))
                    break

                max_timestamp_iso = max(dtlist).strftime("%Y-%m-%dT%H:%M:%S.%f")[:] + 'Z'
                set_iso_timestamp_of_last_consumed_entity(C1Entity().get_table_name(), "process1", max_timestamp_iso)
            else:
                done = True

        self.assertTrue(True)
            
if __name__ == '__main__':
    unittest.main()
