import os
from dotenv import load_dotenv
import json
from common.entity_store import EntityStore
from common.fitness.member_workout_entity import MemberWorkoutDefinitionEntity, MemberWorkoutInstanceEntity, WorkoutDefinitionEntity
from common.table_store import TableStore
from common.blob_store import BlobStore



from common.entity_store import EntityObject
from common.fitness.entities_getter import get_entity
from common.fitness.hx_common import hx_render_template


class WorkoutDefinitionBackupEntity (WorkoutDefinitionEntity):
    table_name="WorkoutDefinitionBackupTable"

    def __init__(self, d={}):
        super().__init__(d)

class MemberWorkoutDefinitionBackupEntity (MemberWorkoutDefinitionEntity):
    table_name="MemberWorkoutDefinitionBackupTable"

    def __init__(self, d={}):
        super().__init__(d)

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

def convert_workout_tables_1_to_2():
    es = EntityStore()
    for wt in [WorkoutDefinitionBackupEntity, MemberWorkoutDefinitionBackupEntity, MemberWorkoutInstanceBackupEntity]:
        print(f"Converting workout tables for {wt.table_name}")
        workouts = get_workouts(es, wt())
        print(f"Found {len(workouts)} workouts to migrate")
        for w in workouts:
            print('.', end='', flush=True)
            updated_ws = convert_workout_section(w['workout_sections'])
            w['workout_sections'] = updated_ws
            es.upsert_item(w)

def backup_workout_tables():
    es = EntityStore()

    workouts = get_workouts(es, WorkoutDefinitionEntity())
    print(f"Found {len(workouts)} workouts to migrate")
    for w in workouts:
        print('.', end='', flush=True)
        bu = WorkoutDefinitionBackupEntity(w)
        es.upsert_item(bu)

    workouts = get_workouts(es, MemberWorkoutDefinitionEntity())
    print(f"Found {len(workouts)} workouts to migrate")
    for w in workouts:
        print('.', end='', flush=True)
        bu = MemberWorkoutDefinitionBackupEntity(w)
        es.upsert_item(bu)

    workouts = get_workouts(es, MemberWorkoutInstanceEntity())
    print(f"Found {len(workouts)} workouts to migrate")
    for w in workouts:
        print('.', end='', flush=True)
        bu = MemberWorkoutInstanceBackupEntity(w)
        es.upsert_item(bu)


def convert_parameter_dict(param_dict):
    """
    the parameters dict looks like this example:
        "parameters": {
            "sets": "1",
            "reps": "10",
            "weight": null,
            "time": null,
            "weight_unit": "lbs",
            "tempo": null
        }
        I need to convert the key names to new key names, as well as I  need to add additional keys
        This is how the existing keys should be converted:
        {
            'sets': 'S',
            'reps': 'R',
            'time': 'T',
            'weight': 'F',
            'weight_unit': 'Fu',
            'tempo': 'P'
        }
        In addition to the above, we also need to add the following keys with null values if they don't exist:  [ 'Tu', 'D', 'Du', 'Fu', 'P', 'Pu']
        In the end, the new parameters dict should look like this:
        {
            'S': '1',
            'R': '10',
            'T': null,
            'Tu': null,
            'F': null,
            'Fu': 'lbs',
            'D': null,
            'Du': null,
            'P': null,
            'Pu': null        
        }
    write the code to convert the old parameters dict to the new parameters dict
    """
    param_map = {
        'sets': 'S',
        'reps': 'R',
        'time': 'T',
        'weight': 'F',
        'weight_unit': 'Fu',
        'tempo': 'P'
    }
    new_param_dict = {}
    for old_key, new_key in param_map.items():
        new_param_dict[new_key] = param_dict.get(old_key, None)
    # Add new keys with null values if they don't exist
    for new_key in ['Tu', 'D', 'Du', 'Fu', 'P', 'Pu']:
        if new_key not in new_param_dict:
            new_param_dict[new_key] = None
    return new_param_dict


def convert_workout_section(workout_sections):
    for section in workout_sections:
        for ex_item in section.get('exercises', []):
            if 'parameters' in ex_item:
                ex_item['parameters'] = convert_parameter_dict(ex_item['parameters'])
    return workout_sections

if __name__ == '__main__':
    # Initialize the environment and r
    init()
    # only need to backup once
    # backup_workout_tables()
    convert_workout_tables_1_to_2()
