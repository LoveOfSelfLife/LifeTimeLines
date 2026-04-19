from datetime import datetime

from common.entity_store import EntityObject
from common.entity_store import EntityStore
from common.fitness.utils import generate_id
from common.utils import IDGenerator

class CoachTeamEntity(EntityObject):
    table_name = "CoachTeamTable"
    fields = ["id", "coach_id", "team_id", "assigned_date"]
    key_field = "id"
    partition_field = "coach_id"

    def __init__(self, d={}):
        super().__init__(d)

def get_coachs_teams(coach_id):
    """Get all teams that a coach is assigned to"""
    es = EntityStore()
    coach_teams = []
    for ct in es.list_items(CoachTeamEntity({"coach_id": coach_id})):
        coach_teams.append(ct)
    return coach_teams

def get_team_coaches(team_id):
    """Get all coaches assigned to a specific team"""
    es = EntityStore()
    # Need to scan all partitions to find coaches of this team
    all_coach_teams = []
    for ct in es.list_items(CoachTeamEntity()):
        if ct.get("team_id") == team_id:
            all_coach_teams.append(ct)
    return all_coach_teams

def assign_coach_to_team(coach_id, team_id):
    """Assign a coach to a team"""
    es = EntityStore()
    
    # Check if coach is already assigned to the team
    existing = es.list_items(CoachTeamEntity({"coach_id": coach_id}))
    for ct in existing:
        if ct.get("team_id") == team_id:
            return ct

    # Create new assignment
    # set the assigned_date field to the current timestamp when creating the assignment
    assignment = CoachTeamEntity({
        "id": IDGenerator.gen_id(),
        "coach_id": coach_id,
        "team_id": team_id,
        "assigned_date": datetime.now().isoformat()
    })
    
    es.upsert_item(assignment)
    return assignment

def remove_coach_from_team(coach_id, team_id):
    """Remove a coach from a team by setting status to inactive"""
    from common.entity_store import EntityStore
    es = EntityStore()
    
    coach_teams = es.list_items(CoachTeamEntity({"coach_id": coach_id}))
    for ct in coach_teams:
        if ct.get("team_id") == team_id:
            es.delete_item(CoachTeamEntity(ct))
            return True

    return False