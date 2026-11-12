from common.entity_store import EntityObject
from common.app_info import get_current_app_id

class TeamEntity(EntityObject):
    table_name = "TeamTable"
    fields = ["id", "app", "name", "location", "description", "created_date", "status"]
    key_field = "id"
    partition_field = "app"

    def __init__(self, d={}):
        super().__init__(d)

def get_teams_list():
    from common.entity_store import EntityStore
    es = EntityStore()
    teams = []
    for t in es.list_items(TeamEntity({"app": get_current_app_id()})):
        teams.append(t)
    return teams

def get_team_by_id(team_id):
    from common.entity_store import EntityStore
    es = EntityStore()
    team = es.get_item(TeamEntity({"app": get_current_app_id(), "id": team_id}))
    return team

def save_team(team_data):
    from common.entity_store import EntityStore
    es = EntityStore()
    team = TeamEntity({**team_data, "app": get_current_app_id()})
    es.upsert_item(team)
    return team