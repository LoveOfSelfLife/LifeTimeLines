"""
Roles service component for team/member query APIs and role-based functionality.
This service provides a centralized API for managing roles and team relationships.
"""

from flask import session
from common.fitness.member_entity import get_user_profile
from common.fitness.team_entity import get_team_by_id, get_teams_list
from common.fitness.member_team_entity import get_members_teams, get_team_members
from common.fitness.coach_team_entity import get_coachs_teams, get_team_coaches

# Session key for storing selected team
SELECTED_TEAM_SESSION_KEY = 'selected_team_id'

def get_current_member_id_from_context(context):
    """Extract member ID from auth context"""
    from common.fitness.member_entity import get_member_id_from_user_context
    return get_member_id_from_user_context(context)

def get_member_role(member_id):
    """Get the role of a member"""
    member = get_user_profile(member_id)
    return member.get('role', 'client') if member else 'client'

def is_member_admin(member_id):
    """Check if member is admin (level >= 10)"""
    from common.fitness.member_entity import is_member_an_admin
    return is_member_an_admin(member_id)

def is_member_coach(member_id):
    """Check if member has coach role"""
    return get_member_role(member_id) == 'coach'

def is_member_client(member_id):
    """Check if member has client role"""
    return get_member_role(member_id) == 'client'

def get_primary_team_id_for_context():
    """Get the primary team ID for the current context (session-based for coaches)"""
    return session.get(SELECTED_TEAM_SESSION_KEY)

def set_primary_team_id_for_context(team_id):
    """Set the primary team ID for the current context"""
    session[SELECTED_TEAM_SESSION_KEY] = team_id

def get_teams_managed_by_coach(coach_id):
    """Get list of teams managed by a coach"""
    if not is_member_coach(coach_id):
        return []
    
    coach_teams = get_coachs_teams(coach_id)
    teams = []
    for ct in coach_teams:
        team = get_team_by_id(ct['team_id'])
        if team:
            teams.append(team)
    return teams

def get_team_for_client(client_id):
    """Get the team that a client belongs to (clients can only be on one team)"""
    if not is_member_client(client_id):
        return None
    
    member_teams = get_members_teams(client_id)
    if member_teams:
        # Client should only be on one team, return the first active one
        return get_team_by_id(member_teams[0]['team_id'])
    return None

def get_team_members_with_details(team_id):
    """Get all members of a team with their full member details"""
    member_teams = get_team_members(team_id)
    members_with_details = []
    
    for mt in member_teams:
        member = get_user_profile(mt['member_id'])
        if member:
            # Combine team membership info with member details
            member_info = dict(member)
            member_info['team_joined_date'] = mt.get('joined_date')
            member_info['team_status'] = mt.get('status')
            members_with_details.append(member_info)
    
    return members_with_details

def get_team_coaches_with_details(team_id):
    """Get all coaches of a team with their full member details"""
    coach_teams = get_team_coaches(team_id)
    coaches_with_details = []
    
    for ct in coach_teams:
        coach = get_user_profile(ct['coach_id'])
        if coach:
            # Combine team assignment info with coach details
            coach_info = dict(coach)
            coach_info['team_assigned_date'] = ct.get('assigned_date')
            coach_info['team_status'] = ct.get('status')
            coaches_with_details.append(coach_info)
    
    return coaches_with_details

def get_current_team_context(member_id):
    """
    Get the current team context for a member based on their role:
    - For clients: return their team (they can only be on one)
    - For coaches: return selected team from session, or first team if none selected
    - For admins: return selected team from session or None
    """
    role = get_member_role(member_id)
    
    if role == 'client':
        return get_team_for_client(member_id)
    elif role == 'coach':
        # Check session for selected team
        selected_team_id = get_primary_team_id_for_context()
        if selected_team_id:
            team = get_team_by_id(selected_team_id)
            # Verify coach is actually assigned to this team
            coach_teams = get_teams_managed_by_coach(member_id)
            if team and any(t['id'] == selected_team_id for t in coach_teams):
                return team
        
        # No valid selection, return first team
        coach_teams = get_teams_managed_by_coach(member_id)
        if coach_teams:
            # Auto-select first team
            set_primary_team_id_for_context(coach_teams[0]['id'])
            return coach_teams[0]
    
    # Admin or no team context
    return None

def get_accessible_members_for_context(member_id):
    """
    Get list of members accessible to the current member based on team context:
    - Clients see members of their team
    - Coaches see members of their current team context
    - Admins see all members (no team filtering)
    """
    if is_member_admin(member_id):
        # Admin sees all members
        from common.fitness.member_entity import get_members_list
        return get_members_list()
    
    current_team = get_current_team_context(member_id)
    if current_team:
        members = get_team_members_with_details(current_team['id'])
        coaches = get_team_coaches_with_details(current_team['id'])
        return members + coaches
    
    # No team context, return empty list
    return []

def can_member_access_team(member_id, team_id):
    """Check if a member can access data for a specific team"""
    if is_member_admin(member_id):
        return True
    
    role = get_member_role(member_id)
    
    if role == 'client':
        # Clients can only access their own team
        client_team = get_team_for_client(member_id)
        return client_team and client_team['id'] == team_id
    elif role == 'coach':
        # Coaches can access teams they're assigned to
        coach_teams = get_teams_managed_by_coach(member_id)
        return any(t['id'] == team_id for t in coach_teams)
    
    return False

def get_member_role_context(member_id):
    """
    Get comprehensive role context for a member including:
    - Role, admin status
    - Current team context
    - Available teams (for coaches)
    - Team selection capability
    """
    role = get_member_role(member_id)
    is_admin = is_member_admin(member_id)
    current_team = get_current_team_context(member_id)
    
    context = {
        'member_id': member_id,
        'role': role,
        'is_admin': is_admin,
        'current_team': current_team,
        'available_teams': [],
        'can_select_team': False
    }
    
    if role == 'coach':
        available_teams = get_teams_managed_by_coach(member_id)
        context['available_teams'] = available_teams
        context['can_select_team'] = len(available_teams) > 1
    
    return context