import os
from dotenv import load_dotenv
import unittest
from common.entity_store import EntityStore
from common.fitness.coach_team_entity import CoachTeamEntity
from common.table_store import TableStore

class TestEntityStore(unittest.TestCase):

    def setUp(self) -> None:
        print(f"setUp()")
        load_dotenv('../.env')
        print(f"{os.getcwd()}")
        print( f"{os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING')}")
        TableStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))

        return super().setUp()
    
    def test_entitystore_list_items(self):

        estore = EntityStore()

        coaches = estore.list_items(CoachTeamEntity())
        count = 0
        for l in coaches:
            count += 1
        print(f"count: {count}")


    def test_get_coachs_teams(self):
        es = EntityStore()
        all_coach_teams = []
        for ct in es.list_items(CoachTeamEntity()):
            all_coach_teams.append(ct)
        print(f"All coach teams: {all_coach_teams}")        


if __name__ == '__main__':
    unittest.main()
