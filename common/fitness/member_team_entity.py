from common.entity_store import EntityObject
from common.utils import IDGenerator
from datetime import datetime
from common.entity_store import EntityStore

class MemberTeamEntity(EntityObject):
    table_name = "MemberTeamTable"
    fields = ["id", "member_id", "team_id", "joined_date"]
    key_field = "id"
    partition_field = "team_id"

    def __init__(self, d={}):
        super().__init__(d)

def get_members_teams(member_id):
    """Get all teams that a member belongs to - should only be one for clients, can be multiple for coaches/admins"""
    es = EntityStore()
    member_teams = []
    for mt in es.list_items(MemberTeamEntity()):
        if mt.get("member_id") == member_id:
            member_teams.append(mt)
    return member_teams

def get_team_members(team_id):
    """Get all members of a specific team"""
    es = EntityStore()
    # Need to scan all partitions to find members of this team
    all_members_of_team = []
    for mt in es.list_items(MemberTeamEntity({ "team_id": team_id })):
        all_members_of_team.append(mt)
    return all_members_of_team

def get_members_team_members(member_id):
    """Get all members that are on the same team(s) as the given member"""
    member_teams = get_members_teams(member_id)
    team_members = []
    for mt in member_teams:
        team_id = mt.get("team_id")
        members_of_team = get_team_members(team_id)
        team_members.extend(members_of_team)
    # Remove duplicates (in case member is on multiple teams with overlapping members)
    unique_team_members = { tm.get("member_id"): tm for tm in team_members }.values()
    return list(unique_team_members)

def add_member_to_team(member_id, team_id):
    """Add a member to a team"""
    es = EntityStore()
    
    # Check if member is already on the team
    existing = es.list_items(MemberTeamEntity({"team_id": team_id}))
    for mt in existing:
        if mt.get("member_id") == member_id:
            return mt                        
    
    # Create new membership
    membership = MemberTeamEntity({
        "id": IDGenerator.gen_id(),
        "member_id": member_id,
        "team_id": team_id,
        "joined_date": datetime.now().isoformat()
    })
    
    es.upsert_item(membership)
    return membership

def remove_member_from_team(member_id, team_id):
    """Remove a member from a team by deleting the membership record"""
    es = EntityStore()
    
    member_teams = es.list_items(MemberTeamEntity({"team_id": team_id}))
    
    for mt in member_teams:
        if mt.get("member_id") == member_id:
            es.delete_item(MemberTeamEntity(mt))
            return True
    
    return False
