import os
from dotenv import load_dotenv
import json
from common.entity_store import EntityStore
from common.fitness.entities_getter import get_entity
from common.fitness.exercise_entity import ExerciseEntity
from common.fitness.member_program_entity import MemberProgramEntity
from common.fitness.member_workout_entity import MemberWorkoutDefinitionEntity, MemberWorkoutInstanceEntity, WorkoutDefinitionEntity
from common.fitness.program_entity import ProgramEntity
from common.fitness.workout_entity import ProgramWorkoutEntity, ProgramWorkoutInstanceEntity, WorkoutEntity
from common.table_store import TableStore
from common.blob_store import BlobStore
from common.fitness.exercises_loader import load_exercise_into_index_table, exercise_generator, load_exercises
from common.fitness.exercise_entity import ExerciseIndexEntity


def init():
    # load_dotenv('D:/GitHub/DickKemp/LifeTimeLines/test/.env')
    load_dotenv('.env')
    print(f"Current working directory: {os.getcwd()}")
    TableStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))
    BlobStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))

def get_programs(es):
    programs = []
    for program in es.list_items(ProgramEntity()):
        programs.append(program)
    return programs

def convert_tables_1_to_2():
    es = EntityStore()

    programs = get_programs(es)
    print(f"Found {len(programs)} programs to migrate")
    for pr in programs:
        mbr_prog = MemberProgramEntity()
        mbr_prog["id"] = pr["id"]
        mbr_prog["member_id"] = pr["member_id"]
        mbr_prog["name"] = pr["name"]
        mbr_prog["created_ts"] = pr.get("Timestamp", '')
        mbr_prog["description"] = pr.get("description", '')
        mbr_prog["start_date"] = pr.get("start_date", '')
        mbr_prog["end_date"] = pr.get("end_date", '')
        es.upsert_item(mbr_prog)
        _ = ProgramWorkoutInstanceEntity()
        for wi in pr.get('workout_instances', []):
            prog_wkt_inst = es.get_item_by_composite_key(wi['program_workout_instance_key'])
            mbr_wkt_inst = MemberWorkoutInstanceEntity()

            mbr_wkt_inst["id"] = prog_wkt_inst["id"]
            mbr_wkt_inst["member_id"] = pr["member_id"]
            mbr_wkt_inst["workout_sections"] = prog_wkt_inst["sections"]
            mbr_wkt_inst["started_ts"] = wi.get("started_ts", '')
            mbr_wkt_inst["finished_ts"] = wi.get("finished_ts", '')
            if wi.get("scheduled_workout_event_id", None) is not None:
                mbr_wkt_inst["scheduled_workout_event_id"] = wi.get("scheduled_workout_event_id", '')
            if wi.get("adjustments_for_next_workout", None) is not None:
                mbr_wkt_inst["adjustments_for_next_workout"] = wi.get("adjustments_for_next_workout", '')
            
            mbr_wkt_inst["member_id"] = pr["member_id"]
            mbr_wkt_inst["member_workout_def_id"] = prog_wkt_inst.get("program_workout_id", '')
            mbr_wkt_inst["member_program_id"] = mbr_prog["id"]
            # print(f"Upserting member workout instance {mbr_wkt_inst['id']} for member {mbr_wkt_inst['member_id']}")
            es.upsert_item(mbr_wkt_inst)

        _ =MemberWorkoutDefinitionEntity()
        _ =ProgramWorkoutEntity()
        for w in pr['workouts']:
            prog_wkt = es.get_item_by_composite_key(w['key'])
            mbr_wkt_def = MemberWorkoutDefinitionEntity()
            mbr_wkt_def['id'] = prog_wkt['id']
            mbr_wkt_def['member_id'] = pr['member_id']
            mbr_wkt_def['description'] = prog_wkt.get('description', '')
            mbr_wkt_def['name'] = prog_wkt.get('name', '')
            mbr_wkt_def['base_workout_def_id'] = prog_wkt.get('parent_workout_id', '')
            mbr_wkt_def['created_ts'] = prog_wkt.get('created_ts', '')
            mbr_wkt_def['created_by'] = prog_wkt.get('created_by', '')
            mbr_wkt_def['tags'] = []
            mbr_wkt_def['member_program_id'] = pr['id']
            mbr_wkt_def['workout_sections'] = prog_wkt.get('sections', [])
            es.upsert_item(mbr_wkt_def)

    # convert workouts
    _ = WorkoutDefinitionEntity()
    workouts = es.list_items(WorkoutEntity())    
    for w in workouts:
        wd = WorkoutDefinitionEntity()
        wd["id"] = w["id"]
        wd["name"] = w["name"]
        wd["workout_sections"] = w["sections"]
        wd["created_ts"] = w.get("created_ts", '')
        wd["created_by"] = w.get("created_by", '')
        wd["type"] = w.get("type", '')
        es.upsert_item(wd)


if __name__ == '__main__':
    # Initialize the environment and r
    init()
    convert_tables_1_to_2()
