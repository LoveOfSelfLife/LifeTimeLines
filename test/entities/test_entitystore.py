
import os
from dotenv import load_dotenv
import unittest
import json
from common.entities.journal_day import JournalDay
# from common.entities.entity import EntityObject
from common.entities.location import LocationEntity
from common.entities.person import GenericEntity, PersonEntity
from common.entity_store import EntityStore
from common.table_store import TableStore


class TestEntityStore(unittest.TestCase):


    def setUp(self) -> None:
        print(f"setUp()")
        load_dotenv('test/.env')
        print(f"{os.getcwd()}")
        print( f"{os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING')}")
        TableStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))

        return super().setUp()
    def test_day_store(self):
        print(f"test1")
        jdlist = []
        jfile = 'test/entities/sample_journal_days.json'
        with open(jfile, "r") as jfd:
            je_list = json.load(jfd)
            for j in je_list:
                jd = JournalDay(j)
                jdlist.append(jd)

        storage = EntityStore()
        storage.upsert_items(jdlist)

        retrieved_items = storage.list_items(JournalDay())
        for r in retrieved_items:
            print(r)

        self.assertTrue(True)
    
    def test_entitystore_list_items(self):

        storage = EntityStore()

        locations = storage.list_items(LocationEntity())
        print(list(storage.list_items(LocationEntity())))
        persons = storage.list_items(PersonEntity())
        for p in persons:
            print(f"person: {p}")

    def test_entitystore_upsert_delete(self):
        storage = EntityStore()
        p = {'id': '108', 'aliases': ['lynn', 'lynnie'], 'photos_album': 'Lynn_Photos_Album'}
        pe = PersonEntity(p)
        storage.upsert_item(pe)
        pel = storage.list_items(PersonEntity())
        print(list(pel))
        pe_got = storage.get_item(PersonEntity({'id': '108'}))
        print(pe_got)
        storage.delete(['108'], PersonEntity)
        pel2 = storage.list_items(PersonEntity())
        print(list(pel2))
        self.assertTrue(True)

    def test_filters(self):
        storage = EntityStore()

        ge = GenericEntity({ "type" : "persons" })
        gel = storage.list_items(ge)
        
        import json
        for g in gel:
            print(json.dumps(g, indent=4))
        # print(list(gel))
        print("Filtering")
                                                             
        # gel = storage.list_items(ge, filter="photos_album eq 'Someones_Photo_Album'")
        gel = storage.list_items(ge, filter="city eq 'pocono pines'")
        # gel = storage.list_items(ge, filter="photos_album eq '""John_Masons_Photo_Album""'")
        for g in gel:
            print(json.dumps(g, indent=4))
                                               
        gel = storage.list_items(ge, filter="city eq 'pocono pines'", newer_than_cutoff_ts_iso='2024-03-06T18:24:23Z')

        print("Filtering by timestamp")
        for g in gel:
            print(json.dumps(g, indent=4))

        gel = storage.list_items(ge, newer_than_cutoff_ts_iso='2024-03-06T18:24:23Z')

        print("Filtering by just timestamp")
        for g in gel:
            print(json.dumps(g, indent=4))

if __name__ == '__main__':
    unittest.main()
