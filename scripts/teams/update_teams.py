import os
from dotenv import load_dotenv
import json
from common.coach_team_entity import CoachTeamEntity
from common.entity_store import EntityStore
from common.entities_getter import get_entity
from common.fitness.exercise_entity import ExerciseEntity
from common.fitness.member_program_entity import MemberProgramsEntity
from common.fitness.member_workout_entity import MemberWorkoutDefinitionEntity, MemberWorkoutInstanceEntity
from common.member_entity import MemberEntity
from common.member_team_entity import MemberTeamEntity
from common.team_entity import TeamEntity
from common.table_store import TableStore
from common.blob_store import BlobStore
from common.fitness.exercises_loader import load_exercise_into_index_table, exercise_generator, load_exercises
from common.fitness.exercise_entity import ExerciseIndexEntity

def init():
    load_dotenv('../.env')
    print(f"Current working directory: {os.getcwd()}")
    TableStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))
    BlobStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))

def update_tables():
    es = EntityStore()
    teams = es.list_items(TeamEntity())
    n = 0
    for t in teams:
        if t.get('app', None) == 'team':
            t['app'] = 'fitnessclub'
            t2 = TeamEntity(t)
            es.upsert_item(t2)
            n += 1
    print(f"Updated {n} teams.")

    member_teams = es.list_items(MemberTeamEntity())
    n = 0
    for mt in member_teams:
        if mt.get('app', None) != 'fitnessclub':
            team_id = mt.get('app')
            mt['app'] = 'fitnessclub'
            mt['team_id'] = team_id
            mt2 = MemberTeamEntity(mt)
            es.upsert_item(mt2)
            n += 1
    print(f"Updated {n} member teams.")

    coach_teams = es.list_items(CoachTeamEntity())
    n = 0
    for ct in coach_teams:
        if ct.get('app', None) != 'fitnessclub':
            team_id = ct.get('app')
            ct['app'] = 'fitnessclub'
            ct['team_id'] = team_id
            ct2 = CoachTeamEntity(ct)
            es.upsert_item(ct2)
            n += 1
    print(f"Updated {n} coach teams.")

    # with open('local/teams2.json', 'w') as f:
    #     json.dump([e for e in teams], f, indent=4)
if __name__ == "__main__":
    init()
    update_tables()
