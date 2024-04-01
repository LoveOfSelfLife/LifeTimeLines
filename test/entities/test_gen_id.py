
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
from common.id_generator import IDGenerator

class TestGenId(unittest.TestCase):


    def setUp(self) -> None:
        print(f"setUp()")
        load_dotenv('test/.env')
        print(f"{os.getcwd()}")
        print( f"{os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING')}")
        TableStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))
        return super().setUp()

    def test_gen(self):
        print(f"test1")
        id1 = IDGenerator.get_unique_id()
        id2 = IDGenerator.get_unique_id("def")
        print(f"id1: {id1}, id2: {id2}")

if __name__ == '__main__':
    unittest.main()
