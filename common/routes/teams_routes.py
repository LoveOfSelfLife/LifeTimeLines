# Team Management Routes

from flask import json, jsonify, make_response, redirect, render_template, request, session, abort, url_for
from common.app_info import get_current_app_id

from common.blueprint import create_blueprint
from common.auth import auth
from common.card_presentation import build_card_views
from common.coach_team_entity import assign_coach_to_team, remove_coach_from_team

from common.entities_getter import filter_entities_by_member_role, get_entities
from common.filter_funcs import get_entity_view_from_request, get_filter_terms_from_request
from common.list_presentation import listing_fields
from common.member_entity import get_member_id_from_user_context, get_members_list
from common.roles_service import get_member_role
from common.team_entity import TeamEntity, get_team_by_id, get_teams_list, save_team
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
@bp.route('/teams-listing', methods=['GET', 'POST'])
@auth.login_required
def teams_listing(context=None):
    member_id = get_member_id_from_user_context(context)
    if not member_id:
        abort(401)
    page = int(request.args.get('page', 1))
    filter_terms = get_filter_terms_from_request(TeamEntity.table_name)

    return teams_listing2(context, member_id, page=page, filter_terms=filter_terms)

def teams_listing2(context=None, member_id=None, page=1, filter_terms=None):
    entity_name = TeamEntity.table_name
    if not member_id:
        member_id = get_member_id_from_user_context(context)
        if not member_id:
            abort(401)
    if filter_terms is None:
        filter_terms = get_filter_terms_from_request(entity_name)
    view = get_entity_view_from_request(TeamEntity.table_name)
    fields_to_display = listing_fields(TeamEntity.list_presentation)
    entities = get_entities(TeamEntity.table_name, fields_to_display, filter_terms, partition_key=get_current_app_id(), member_id=member_id)
    entities = filter_entities_by_member_role(member_id, entities)
    target = request.args.get('target', None)
    page_size = 100  # Define the number of entities per page
    total_pages = (len(entities) + page_size - 1) // page_size
    start = (page - 1) * page_size
    end = start + page_size
    current = entities[start:end]
    if view == 'card':
        current = build_card_views(current, TeamEntity.card_presentation)

    if request.headers.get('HX-Target') == 'results-area':
        template_file_name = 'entity_results_partial.html'
    else:
        template_file_name = 'entity_list_component.html'

    # Set results_target_container based on target parameter
    results_target_container = target if target else 'results-area'
    entities_listing_route = f'/teams?target={results_target_container}'

    entity_action_route = f'/teams/edit?entity_table={entity_name}'
    entity_action_icon='bi-pencil-square'
    entity_action_route_method = None
    entity_action_route_target = None
    entity_action_label='Edit Team'

    entity_add_route = f"{url_for('teams.create_team')}?x=1"


    template_data = dict(
        title="Teams Library",
        fields_to_display=fields_to_display,
        main_content_container="entities-container",
        entities=current,
        entity_name=entity_name,
        filter_terms=filter_terms,
        args=request.args,
        page=page,
        view=view,
        total_pages=total_pages,
        entity_add_route=entity_add_route,
        entities_listing_route=entities_listing_route,
        entity_view_route=None,
        entity_action_route=entity_action_route,
        entity_action_route_method=entity_action_route_method,
        entity_action_route_target=entity_action_route_target,
        entity_action_icon=entity_action_icon,
        entity_action_label=entity_action_label,
        favorite_toggle_route='/favorites/toggle',
        results_target_container=results_target_container,
        entity_card_view_html='entity_card_view.html',
        card_actions=[
            {
                'id': 'edit', 'enabled': bool(entity_action_route),
                'url': entity_action_route, 'method': 'get', 'target': 'entities-container',
                'icon': 'bi-pencil-square', 'label': 'Edit Team', 'button_label': 'Edit',
            },
        ],
        context=context,
    )
    return hx_render_template(template_file_name, **template_data)

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


@bp.route('/edit')
@auth.login_required
def edit_team(context=None):
    team_id = request.args.get('key')
    return manage_team2(team_id, context=context)

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
            existing_teams = get_members_teams(member_id, get_current_app_id())
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
