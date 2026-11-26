from common.entity_store import EntityObject
from common.app_info import get_current_app_id
def team_default_image_url():
    return "/static/images/default_team_image.png"

class TeamEntity(EntityObject):
    table_name = "TeamTable"
    fields = ["id", "app", "name", "location", "description", "created_date", "status", "image_url"]
    key_field = "id"
    partition_field = "app"
    list_presentation = (
        {"label": "Name", "value": lambda entity: entity.get("name")},
        {"label": "Location", "value": lambda entity: entity.get("location")},
        {"label": "Description", "value": lambda entity: entity.get("description")},
    )
    card_presentation = {
        "title": lambda entity: entity.get("name", ""),
        "image": lambda entity: entity.get("image_url", team_default_image_url()),
        "fields": (
            {"label": "Location", "value": lambda entity: entity.get("location")},
            {"label": "Description", "value": lambda entity: entity.get("description")},
        ),
        "actions": ("edit",)
    }

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