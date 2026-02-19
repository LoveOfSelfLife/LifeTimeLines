import os
import json
from flask import Blueprint, abort, jsonify, make_response, render_template, request, redirect, session, url_for
import requests
from auth import auth
from common.fitness.active_fitness_registry import _get_filter_terms_from_request, get_fitnessclub_entity_filters_for_entity, get_fitnessclub_listing_fields_for_entity, get_entity_obj_from_entity_name, get_fitnessclub_entity_names
from common.env_context import Env
from common.fitness.entities_getter import delete_entity
from common.fitness.exercise_entity import render_exercise_popup_viewer_html
from common.fitness.member_entity import get_member_id_from_user_context, get_members_list
from common.fitness.impersonation import start_impersonation, stop_impersonation, get_impersonated_member_id
from common.fitness.utils import generate_id
from common.fitness.hx_common import hx_render_template
from common.entity_store import EntityStore
from common.fitness.entities_getter import get_entities
bp = Blueprint('admin', __name__, template_folder='templates')

@bp.route('/')
@auth.login_required
def root(context=None):
    entity_table = request.args.get('entity_table')    
    return redirect(url_for('admin.entities_listing', entity_table=entity_table), 302)

@bp.route('/entities-listing', methods=['GET', 'POST'])
@auth.login_required
def entities_listing(context=None):
    entity_name = request.args.get('entity_table', None)    
    page = int(request.args.get('page', 1))
    page_size = 100

    # Handle view preference
    view = (request.form.get('view') if request.method == 'POST' 
            else request.args.get('view')) or session.get('view_preference', 'list')
    
    if view != session.get('view_preference'):
        session['view_preference'] = view
    
    fields_to_display = get_fitnessclub_listing_fields_for_entity(entity_name)
    filter_terms = _get_filter_terms_from_request()

    member_id = get_member_id_from_user_context(context)
    entities = get_entities(entity_name, fields_to_display, filter_terms, partition_key=member_id)
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

    # return jsonify({
    #     "status": "success",
    #     "message": "JSON saved",
    # }), 200

    response = make_response('')
    response.headers['HX-Trigger'] = json.dumps({
        "entityListChanged": True,
        "showMessage": { "value" : f"item was saved.", "target": "body" }
    })
    response.headers['HX-Redirect'] = f'/admin?entity_table={table_id}'
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
    
