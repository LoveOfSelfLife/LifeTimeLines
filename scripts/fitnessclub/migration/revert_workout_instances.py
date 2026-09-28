import os
from dotenv import load_dotenv
import json
from common.entity_store import EntityStore
from common.fitness.member_workout_entity import MemberWorkoutInstanceEntity
from common.table_store import TableStore
from common.blob_store import BlobStore



from common.entity_store import EntityObject
from common.fitness.entities_getter import get_entity
from common.fitness.hx_common import hx_render_template


class MemberWorkoutInstanceBackupEntity (MemberWorkoutInstanceEntity):
    table_name="MemberWorkoutInstanceBackupTable"

    def __init__(self, d={}):
        super().__init__(d)

def init():
    # load_dotenv('D:/GitHub/DickKemp/LifeTimeLines/test/.env')
    load_dotenv('.env')
    print(f"Current working directory: {os.getcwd()}")
    TableStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))
    BlobStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))

def get_workouts(es, workout_entity_type):
    workouts = []
    for workout in es.list_items(workout_entity_type):
        workouts.append(workout)
    return workouts

def revert_from_workoutInstance_backup_backto_original():
    es = EntityStore()
    for wt in [MemberWorkoutInstanceBackupEntity]:
        workouts = get_workouts(es, wt())
        print(f"Found {len(workouts)} workout instances to migrate")
        for w in workouts:
            print('.', end='', flush=True)
            new_wi = MemberWorkoutInstanceEntity(w)
            es.upsert_item(new_wi)


if __name__ == '__main__':

    init()
    revert_from_workoutInstance_backup_backto_original()
