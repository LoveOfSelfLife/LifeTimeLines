# Team Management Routes

from flask import json, jsonify, make_response, redirect, render_template, request, session, abort

from common.blueprint import create_blueprint
from common.auth import auth
from common.coach_team_entity import assign_coach_to_team, remove_coach_from_team

from common.member_entity import get_member_id_from_user_context, get_members_list
from common.roles_service import get_member_role
from common.team_entity import get_team_by_id, get_teams_list, save_team
from common.template_renderer import hx_render_template

from datetime import datetime
from common.coach_team_entity import get_team_coaches
from common.member_team_entity import get_team_members, get_members_teams
from common.member_team_entity import add_member_to_team
from common.member_team_entity import remove_member_from_team
from common.coach_team_entity import assign_coach_to_team
from common.coach_team_entity import remove_coach_from_team
from common.utils import generate_id
bp = create_blueprint('teams', __name__)

@bp.route('/')
@auth.login_required
def teams_listing(context=None):
    """Admin page for managing teams"""
    return teams_listing2(context=context)

def teams_listing2(context=None):
    """Admin page for managing teams"""
    return hx_render_template('admin/teams_listing.html', 
                              teams=get_teams_list(), 
                              context=context)

@bp.route('/create', methods=['GET', 'POST'])
@auth.login_required
def create_team(context=None):
    """Create a new team"""
    if request.method == 'POST':

        team_data = {
            'id': generate_id('tem'),
            'name': request.form.get('name'),
            'location': request.form.get('location', ''),
            'description': request.form.get('description', ''),
            'created_date': datetime.now().isoformat(),
            'status': 'active'
        }
        
        try:
            save_team(team_data)
            response = make_response(teams_listing2(context=context))
            response.headers['HX-Trigger'] = json.dumps({
                "showMessage": {"value": f"Team '{team_data['name']}' created successfully", "target": "body"}
            })
            return response
        except Exception as e:
            return hx_render_template('admin/create_team.html', 
                                      error=str(e), 
                                      form_data=request.form,
                                      context=context)
    
    return hx_render_template('admin/create_team.html', context=context)

@bp.route('/<team_id>/manage')
@auth.login_required
def manage_team(team_id, context=None):
    """Manage team members and coaches"""
    return manage_team2(team_id, context=context)

def manage_team2(team_id, context=None):
    """Manage team members and coaches"""
    team = get_team_by_id(team_id)
    if not team:
        return "Team not found", 404

    # Get current team members and coaches
    team_members = get_team_members(team_id)
    team_coaches = get_team_coaches(team_id)
    
    # Get member details for team members
    members_with_details = []
    for mt in team_members:
        from common.member_entity import get_user_profile
        member = get_user_profile(mt['member_id'])
        if member:
            member_info = dict(member)
            member_info['team_joined_date'] = mt.get('joined_date')
            members_with_details.append(member_info)
    
    # Get member details for team coaches
    coaches_with_details = []
    for ct in team_coaches:
        from common.member_entity import get_user_profile
        coach = get_user_profile(ct['coach_id'])
        if coach:
            coach_info = dict(coach)
            coach_info['team_assigned_date'] = ct.get('assigned_date')
            coaches_with_details.append(coach_info)
    
    # Get all members for potential assignment
    all_members = get_members_list()
    available_members = [m for m in all_members if not any(tm['member_id'] == m['id'] for tm in team_members)]
    available_coaches = [m for m in all_members if get_member_role(m['id']) == 'coach' and not any(tc['coach_id'] == m['id'] for tc in team_coaches)]
    
    return hx_render_template('admin/manage_team.html',
                              team=team,
                              team_members=members_with_details,
                              team_coaches=coaches_with_details,
                              available_members=available_members,
                              available_coaches=available_coaches,
                              context=context)

@bp.route('/<team_id>/add_member', methods=['POST'])
@auth.login_required
def add_member_to_team_route(team_id, context=None):
    response_status = 200
    

    """Add a member to a team"""
    member_id = request.form.get('member_id')
    if not member_id:
        response_message = json.dumps({
                "showMessage": {"value": "Member ID required", "target": "body"}
            })
        response_status = 400
    else:
        # Check if member is already on another team (clients can only be on one team)
        member_role = get_member_role(member_id)
        if member_role == 'client':
            existing_teams = get_members_teams(member_id)
            if len(existing_teams) > 0:
                response_message = json.dumps({
                    "showMessage": {"value": "Client is already on another team. Clients can only be on one team at a time.", "target": "body"}
                })
                response_status = 400

        if response_status == 200:
            add_member_to_team(member_id, team_id)

        response = make_response(manage_team2(team_id, context=context))
        
        if response_status == 200:
            response_message = json.dumps({
                "showMessage": {"value": "Member added to team successfully", "target": "body"}
            })

    response.headers['HX-Trigger'] = response_message
    return response, response_status 

@bp.route('/<team_id>/remove_member', methods=['POST'])
@auth.login_required
def remove_member_from_team_route(team_id, context=None):
    """Remove a member from a team"""
    member_id = request.form.get('member_id')
    if not member_id:
        return "Member ID required", 400
    

    remove_member_from_team(member_id, team_id)
    
    response = make_response(manage_team2(team_id, context=context))
    response.headers['HX-Trigger'] = json.dumps({
        "showMessage": {"value": "Member removed from team successfully", "target": "body"}
    })
    return response

@bp.route('/<team_id>/add_coach', methods=['POST'])
@auth.login_required
def add_coach_to_team_route(team_id, context=None):
    """Assign a coach to a team"""
    coach_id = request.form.get('coach_id')
    if not coach_id:
        return "Coach ID required", 400
    
    assign_coach_to_team(coach_id, team_id)
    
    response = make_response(manage_team2(team_id, context=context))
    response.headers['HX-Trigger'] = json.dumps({
        "showMessage": {"value": "Coach assigned to team successfully", "target": "body"}
    })
    return response

@bp.route('/<team_id>/remove_coach', methods=['POST'])
@auth.login_required
def remove_coach_from_team_route(team_id, context=None):
    """Remove a coach from a team"""
    coach_id = request.form.get('coach_id')
    if not coach_id:
        return "Coach ID required", 400
    
    
    remove_coach_from_team(coach_id, team_id)
    
    response = make_response(manage_team2(team_id, context=context))
    response.headers['HX-Trigger'] = json.dumps({
        "showMessage": {"value": "Coach removed from team successfully", "target": "body"}
    })
    return response
    
@bp.route("/select", methods=["POST"])
@auth.login_required
def select_team(context=None):
    """Allow coaches to select their active team"""
    from common.roles_service import set_primary_team_id_for_context, get_member_role, get_teams_managed_by_coach
    import json
    from flask import make_response
    
    team_id = request.form.get('team_id')
    member_id = get_member_id_from_user_context(context)
    
    if not team_id:
        return "Team ID required", 400
    
    # Verify user is a coach and has access to this team
    if get_member_role(member_id) != 'coach':
        return "Only coaches can select teams", 403
    
    coach_teams = get_teams_managed_by_coach(member_id)
    if not any(t['id'] == team_id for t in coach_teams):
        return "Access denied to this team", 403
    
    # Set the selected team in session
    set_primary_team_id_for_context(team_id)
    
    # Find the team name for the success message
    selected_team = next((t for t in coach_teams if t['id'] == team_id), None)
    team_name = selected_team['name'] if selected_team else team_id
    
    response = make_response('')
    response.headers['HX-Trigger'] = json.dumps({
        "showMessage": {"value": f"Switched to team: {team_name}", "target": "body"}
    })
    response.headers['HX-Refresh'] = 'true'  # Refresh the page to update menu and context
    return response
