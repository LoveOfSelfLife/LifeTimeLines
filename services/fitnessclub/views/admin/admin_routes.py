from datetime import datetime
import os
import json
from flask import Blueprint, abort, jsonify, make_response, render_template, request, redirect, session, url_for
import requests
from auth import auth
from common.fitness.active_fitness_registry import get_fitnessclub_entity_filters_for_entity, get_fitnessclub_listing_fields_for_entity, get_entity_obj_from_entity_name, get_fitnessclub_entity_names
from common.env_context import Env
from common.fitness.entities_getter import delete_entity
from common.fitness.exercise_entity import render_exercise_popup_viewer_html
from common.fitness.member_entity import get_member_id_from_user_context, get_members_list
from common.fitness.team_entity import get_teams_list, get_team_by_id, save_team
from common.fitness.member_team_entity import add_member_to_team, remove_member_from_team, get_team_members
from common.fitness.coach_team_entity import assign_coach_to_team, remove_coach_from_team, get_team_coaches
from common.fitness.roles_service import get_member_role, is_member_coach, is_member_client
from common.fitness.impersonation import start_impersonation, stop_impersonation, get_impersonated_member_id
from common.fitness.utils import generate_id
from common.fitness.hx_common import get_filter_terms_from_request, hx_render_template
from common.entity_store import EntityStore
from common.fitness.entities_getter import get_entities
from common.fitness.member_team_entity import get_members_teams
from common.fitness.favorites_entity import toggle_entity_favorite

bp = Blueprint('admin', __name__, template_folder='templates')

@bp.route('/')
@auth.login_required
def root(context=None):
    entity_table = request.args.get('entity_table')    
    return entities_listing2(context=context, entity_name=entity_table)

@bp.route('/profile')
@auth.login_required
def profile(context=None):
    return entities_listing2(context=context, entity_name='MemberTable')

@bp.route('/entities-listing', methods=['GET', 'POST'])
@auth.login_required
def entities_listing(context=None):
    entity_name = request.args.get('entity_table', None)    
    return entities_listing2(context=context, entity_name=entity_name)


@bp.route('/toggle-favorite', methods=['POST'])
@auth.login_required
def toggle_favorite(context=None):
    member_id = get_member_id_from_user_context(context)
    if not member_id:
        abort(401)

    entity_table = request.form.get('entity_table', None)
    entity_id = request.form.get('entity_id', None)

    if not entity_table or not entity_id:
        abort(400)

    if entity_table not in get_fitnessclub_entity_names():
        abort(404)

    entity = get_entity_obj_from_entity_name(entity_table)
    entity[entity.get_key_field()] = entity_id

    is_favorite = toggle_entity_favorite(entity, member_id)

    item_dom_id = request.form.get('item_dom_id', f'entity-item-{entity_id}')
    favorites_only = str(request.form.get('favorites_only', 'false')).lower() == 'true'

    html = render_template(
        'favorite_entity_toggle.html',
        favorite_entity_id=entity_id,
        favorite_entity_table=entity_table,
        favorite_item_dom_id=item_dom_id,
        favorite_is_active=is_favorite,
        favorite_toggle_route='/admin/toggle-favorite',
        favorites_filter_active=favorites_only
    )

    if favorites_only and not is_favorite:
        dom_id_json = json.dumps(item_dom_id)
        html += f"\n<script>(function(){{const el=document.getElementById({dom_id_json});if(el){{el.remove();}}}})();</script>"

    return html

def entities_listing2(context=None, entity_name=None):
    page = int(request.args.get('page', 1))
    page_size = 100

    # Handle view preference
    view = (request.form.get('view') if request.method == 'POST' 
            else request.args.get('view')) or session.get('view_preference', 'list')
    
    if view != session.get('view_preference'):
        session['view_preference'] = view
    
    fields_to_display = get_fitnessclub_listing_fields_for_entity(entity_name)
    filter_terms = get_filter_terms_from_request()

    member_id = get_member_id_from_user_context(context)
    entities = get_entities(entity_name, fields_to_display, filter_terms, partition_key=member_id, member_id=member_id)
    return render_entity_template(context, entity_name, page, view, page_size, fields_to_display, filter_terms, entities)

def render_entity_template(context, entity_name, page, view, page_size, fields_to_display, filter_terms, entities):
    total_pages = (len(entities) + page_size - 1) // page_size
    start = (page - 1) * page_size
    end = start + page_size
    current = entities[start:end]
    if request.headers.get('HX-Target') == 'results-area':
        template_file_name = 'entity_results_partial.html'
    else:
        template_file_name = 'entity_list_component.html'

    # Set results_target_container based on request args
    target = request.args.get('target')
    results_target_container = target if target else 'results-area'

    return hx_render_template(
        template_file_name,
        entity_name=entity_name,
        main_content_container="entities-container",        
        fields_to_display=fields_to_display,
        entities=current,
        filter_terms=filter_terms,
        args=request.args,
        page=page,
        view=view,
        total_pages=total_pages,
        entity_add_route=f'/admin/add/{entity_name}',
        filter_dialog_route=f'/admin/filter-dialog?entity_table={entity_name}',
        entities_listing_route=f'/admin/entities-listing?entity_table={entity_name}',
        entity_view_route=f'/admin/view?entity_table={entity_name}',
        entity_action_route=f'/admin/edit?entity_table={entity_name}',
        entity_action_icon='bi-pencil-square',
        entity_action_label='Edit',
        favorite_toggle_route='/admin/toggle-favorite',
        results_target_container=results_target_container,
        context=context
    )
@bp.route('/filter-dialog')
@auth.login_required
def filter_dialog(context=None):
    entity_name = request.args.get('entity_table', None)
    if not entity_name:
        return "No table id provided", 404
    if entity_name not in get_fitnessclub_entity_names():
        return "Table not allowed", 404
    entity_type = get_entity_obj_from_entity_name(entity_name)
    filters = get_fitnessclub_entity_filters_for_entity(entity_name)

    return hx_render_template('filter_dialog.html', 
                              entities_listing_route=f'/admin/entities-listing?entity_table={entity_name}',
                              entity_display_name=entity_type.get_display_name(),                              
                              entity_name=entity_name,
                              filters=filters,
                              args=request.args,
                              context=context)

@bp.route('/edit')
@auth.login_required
def edit_entity(context=None):
    table_id = request.args.get('entity_table', None)
    if not table_id:
        return "No table id provided", 404
    if table_id not in get_fitnessclub_entity_names():
        return "Table not allowed", 404
    entity_instance = get_entity_obj_from_entity_name(table_id)
    
    schema = entity_instance.get_schema()

    composite_key_str = request.args.get('key', None)
    composite_key = eval(composite_key_str) if composite_key_str else None
    es = EntityStore()
    entity_to_edit = es.get_item_by_composite_key(composite_key)
    
    if 'Timestamp' in entity_to_edit:
        del(entity_to_edit['Timestamp'])

    # return json.dumps(entity_to_edit)
    return hx_render_template('admin/entity_editor.html', 
                              entity=entity_to_edit, 
                              schema=schema,
                              table_id=table_id, 
                              errors={},
                              upload_file_url=f'/api/upload/{table_id}',
                              update_entity_url=f'/admin/update/{table_id}?key={composite_key}',
                              delete_entity_url=f'/admin/delete/{table_id}?key={composite_key}',
                              context=context)

@bp.route('/view')
@auth.login_required
def view_entity(context=None):
    table_id = request.args.get('entity_table', None)
    if not table_id:
        return "No table id provided", 404
    if table_id not in get_fitnessclub_entity_names():
        return "Table not allowed", 404
    entity_instance = get_entity_obj_from_entity_name(table_id)
    
    schema = entity_instance.get_schema()

    composite_key_str = request.args.get('key', None)
    composite_key = eval(composite_key_str) if composite_key_str else None
    es = EntityStore()
    entity_to_view = es.get_item_by_composite_key(composite_key)
    
    return render_exercise_popup_viewer_html(context, entity_to_view)

@bp.route('/delete/<table_id>', methods=['POST'])
@auth.login_required
def delete_entity_from_table(context=None, table_id=None):
    if not table_id:
        return "No table id provided", 404
    if table_id not in get_fitnessclub_entity_names():
        return "Table not allowed", 404
    entity = get_entity_obj_from_entity_name(table_id)    


    schema = entity.get_schema()

    composite_key_str = request.args.get('key', None)
    composite_key = eval(composite_key_str) if composite_key_str else None

    es = EntityStore()
    entity_to_delete = es.get_item_by_composite_key(composite_key)
    
    if not entity_to_delete:
        return "Entity not found", 404

    delete_entity(entity_to_delete)
    # es.delete_items([entity_to_delete])

    response = make_response('')
    response.headers['HX-Trigger'] = json.dumps({
        "eventListChanged": None,
        "showMessage": { "value" : f"selected item was deleted.", "target": "body" }
    })
    # return response
    return redirect(f'/admin?entity_table={table_id}', 302, response)

@bp.route('/add/<table_id>', methods=['GET'])
@auth.login_required
def existing_entity_editor(context=None, table_id=None):
    if not table_id:
        return "No table id provided", 404
    if table_id not in get_fitnessclub_entity_names():
        return "Table not allowed", 404
    entity = get_entity_obj_from_entity_name(table_id)
    es = EntityStore()
    entity_to_edit = {}
    schema = entity.get_schema()
    composite_key = (entity_to_edit.get('id', None), entity_to_edit.get('partition_value', None), table_id)
    return hx_render_template('admin/entity_editor.html', 
                            entity=entity_to_edit, 
                            schema=schema,
                            table_id=table_id, 
                            errors={},
                            upload_file_url=f'/api/upload/{table_id}',
                            update_entity_url=f'/admin/update/{table_id}',
                            delete_entity_url=f'/admin/delete/{table_id}?key={composite_key}',
                            context=context)
        
@bp.route('/update/<table_id>', methods=['POST'])
@auth.login_required
def update_entity_save_json(context=None, table_id=None):

    # 1) Parse the incoming JSON
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Invalid or missing JSON"}), 400

    print(f"Received JSON payload for table {table_id}: {data}")
    entity = get_entity_obj_from_entity_name(table_id)        

    es = EntityStore()
    
    # this assumes that the entity uses 'id' as the key field
    # it also assumes that the entity has a fixed partition value
    # probably need to make this more generic in the future
    # TODO: fix this to be more generic
    partition_field = entity.get_partition_field()
    if partition_field:
        if partition_field != 'member_id':
            abort(400, "Only Partition field 'member_id' is supported at this time")
            
        member_id = get_member_id_from_user_context(context)
        if not member_id:
            abort(400, "Could not determine member id from user context")
        data['member_id'] = member_id

    # if the entity does not have an id, then generate one
    if not data.get('id', None):
        # Generate a new ID for the entity
        data['id'] = generate_id(data['name'] if 'name' in data else '')

    entity.initialize(data)
    es.upsert_item(entity)

    response = make_response(entities_listing2(context=context, entity_name=table_id))
    response.headers['HX-Trigger'] = json.dumps({
        "showMessage": { "value" : f"item was saved.", "target": "body" }
    })
    return response

@bp.route('/impersonate_dialog')
@auth.login_required
def impersonate_dialog(context=None):
    members = get_members_list()
    current_impersonation_id = get_impersonated_member_id()
    current_impersonated_member = None
    
    if current_impersonation_id:
        current_impersonated_member = next((m for m in members if m.get('id', None) == current_impersonation_id), None)
    
    return render_template('impersonate_dialog.html', 
                         members=members, 
                         current_impersonation=current_impersonation_id,
                         current_impersonated_member=current_impersonated_member)

@bp.route('/start_impersonation', methods=['POST'])
@auth.login_required
def start_impersonation_route(context=None):
    member_id = request.form.get('member_id')
    if member_id:
        start_impersonation(member_id)
        selected_member = next((m for m in get_members_list() if m.get('id', None) == member_id), None)
        member_name = selected_member.get('name', member_id) if selected_member else member_id
        message = f"Now impersonating {member_name}"
    else:
        message = "Please select a member to impersonate"
    
    response = make_response('')
    response.headers['HX-Trigger'] = json.dumps({
        "showMessage": {"value": message, "target": "body"}
    })
    # Redirect to home page to refresh with new impersonation context
    response.headers['HX-Redirect'] = '/'
    return response

@bp.route('/stop_impersonation', methods=['POST'])
@auth.login_required
def stop_impersonation_route(context=None):
    stop_impersonation()
    
    response = make_response('')
    response.headers['HX-Trigger'] = json.dumps({
        "showMessage": {"value": "Stopped impersonation", "target": "body"}
    })
    # Redirect to home page to refresh with normal context
    response.headers['HX-Redirect'] = '/'
    return response

# Team Management Routes

@bp.route('/teams')
@auth.login_required
def teams_listing(context=None):
    """Admin page for managing teams"""
    return teams_listing2(context=context)

def teams_listing2(context=None):
    """Admin page for managing teams"""
    return hx_render_template('teams_listing.html', 
                              teams=get_teams_list(), 
                              context=context)

@bp.route('/teams/create', methods=['GET', 'POST'])
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
            return hx_render_template('create_team.html', 
                                      error=str(e), 
                                      form_data=request.form,
                                      context=context)
    
    return hx_render_template('create_team.html', context=context)

@bp.route('/teams/<team_id>/manage')
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
        from common.fitness.member_entity import get_user_profile
        member = get_user_profile(mt['member_id'])
        if member:
            member_info = dict(member)
            member_info['team_joined_date'] = mt.get('joined_date')
            members_with_details.append(member_info)
    
    # Get member details for team coaches
    coaches_with_details = []
    for ct in team_coaches:
        from common.fitness.member_entity import get_user_profile
        coach = get_user_profile(ct['coach_id'])
        if coach:
            coach_info = dict(coach)
            coach_info['team_assigned_date'] = ct.get('assigned_date')
            coaches_with_details.append(coach_info)
    
    # Get all members for potential assignment
    all_members = get_members_list()
    available_members = [m for m in all_members if not any(tm['member_id'] == m['id'] for tm in team_members)]
    available_coaches = [m for m in all_members if get_member_role(m['id']) == 'coach' and not any(tc['coach_id'] == m['id'] for tc in team_coaches)]
    
    return hx_render_template('manage_team.html',
                              team=team,
                              team_members=members_with_details,
                              team_coaches=coaches_with_details,
                              available_members=available_members,
                              available_coaches=available_coaches,
                              context=context)

@bp.route('/teams/<team_id>/add_member', methods=['POST'])
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

@bp.route('/teams/<team_id>/remove_member', methods=['POST'])
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

@bp.route('/teams/<team_id>/add_coach', methods=['POST'])
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

@bp.route('/teams/<team_id>/remove_coach', methods=['POST'])
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
    
