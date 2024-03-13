
import os
from dotenv import load_dotenv
import unittest
import json
from common.entities.photos import MediaItem
from common.entities.location import LocationEntity
from common.entities.person import GenericEntity, PersonEntity
from common.entity_consumer import _break_up_list_into_ranges_of_size_num, find_unconsumed_entity_ranges
from common.entity_store import EntityStore
from common.table_store import TableStore

class TestEntityDistribution(unittest.TestCase):


    def setUp(self) -> None:
        print(f"setUp()")
        load_dotenv('test/.env')
        print(f"{os.getcwd()}")
        print( f"{os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING')}")
        TableStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))
        return super().setUp()

    
    def test_entitystore_list_items(self):

        storage = EntityStore()

        locations = storage.list_items(MediaItem())
        count = 0
        for l in locations:
            count += 1
        print(f"count: {count}")

    def test_distribution(self):
        from datetime import datetime
   
        tbst = TableStore("MediaItemsTable")
        count=0
        full=[]
        for mi in tbst.query(select=["Timestamp"]):

            count += 1
            full.append(mi.metadata["timestamp"])

        print(f"count: {count}")
        full.sort()
        print(f"full: {full[0:10]}")

    def test_break_ranges(self):
        L = [1,1,1,1,1,2,2,2,2,2,2,2,3,4,5,6,7,8,8,8,8,8,8,8,8,8,9,9,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23]
        L = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23]
        L = [1,2,3,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23]
        L = [1,2,3,3,3,3,3,3,3,3,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23]
        L = [1,2,3,3,3,3,3,3,3,3,3,4,4,5,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23]
        L = [1,2,3,3,3,3,3,3,3,3,3,4,4,5,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,23,23,23,23]
        L = [1,2,3,3,3,3,3,3,3,3,3,4,4,5,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,20,21,22,23,23,23,23,23]        
        L = [1,2,3,3,3,3,3,3,3,3,3,4,4,5,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,20,21,21,22,23,23,23,23,23]        
        L = [1,2,3,3,3,3,3,3,3,3,3,4,4,5,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,20,21,22,22,23,23,23,23,23]                
        L = [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
        L = [1,1,1,1,1,1,1,1,1,1,1,2,1,1,1,1,1]
        ranges = list(_break_up_list_into_ranges_of_size_num(L, 3))
        print(f"L: {L}")
        print(f"ranges: {ranges}")
        print([L[s:e] for s,e in ranges])
        print('-----------------------------------')
        L = [1,2,3,4,5,6,7]
        L = [1,2,3,4,5,6,7,8,9,10]
        L = [1,2,3,4,5,6,7,8,9,10,11]        
        L = [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
        ranges = list(_break_up_list_into_ranges_of_size_num(L, 10))
        print(f"L: {L}")
        print(f"ranges: {ranges}")
        print([L[s:e] for s,e in ranges])

    def test_break_up_entities(self):
        ranges = find_unconsumed_entity_ranges(MediaItem(), "consumer1", 500)
        print(f"ranges: {ranges}")

if __name__ == '__main__':
    unittest.main()
