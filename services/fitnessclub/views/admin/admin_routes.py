from datetime import datetime
import os
import json
from flask import abort, jsonify, make_response, render_template, request, redirect, session, url_for
from common.blueprint import create_blueprint
from common.auth import auth
from common.fitness.active_fitness_registry import get_fitnessclub_listing_fields_for_entity, get_fitnessclub_entity_names
from common.env_context import Env
from common.entities_getter import delete_entity
from common.filter_funcs import get_filter_terms_from_request
from common.template_renderer import hx_render_template
from common.member_entity import get_member_id_from_user_context
from common.utils import generate_id
from common.entity_store import EntityStore, get_entity_obj_from_entity_name
from common.entities_getter import get_entities
from common.app_info import get_current_app_id

bp = create_blueprint('admin', __name__)

# @bp.route('/')
# @auth.login_required
# def root(context=None):
#     entity_table = request.args.get('entity_table')    
#     return entities_listing2(context=context, entity_name=entity_table)

@bp.route('/members', methods=['GET', 'POST'])
@auth.login_required
def members(context=None):
    page = int(request.args.get('page', 1))
    page_size = 100

    # Handle view preference
    view = (request.form.get('view') if request.method == 'POST' 
            else request.args.get('view')) or session.get('view_preference', 'list')
    
    if view != session.get('view_preference'):
        session['view_preference'] = view


    fields_to_display = { 
                      "listing_view": [ "name",
                                               "short_name",
                                               "email",
                                               "role"
                                            ],
                        "card_view": [ "title",
                                             "subtitle",
                                             "image_url",
                                             "description"
                                           ],
                        "field_mapping" :  { "name" : lambda e: e['name'] if 'name' in e else "",
                                             "title" : lambda e: e['name'] if 'name' in e else "",
                                              "subtitle" : lambda e: e['short_name'] if 'short_name' in e else "",
                                              "short_name" : lambda e: e['short_name'] if 'short_name' in e else "",
                                              "role" : lambda e: e['role'] if 'role' in e else "",
                                              "image_url" : lambda e: e['image_url'] if 'image_url' in e else "",
                                              "description" : lambda e: f"{e['email']} ({e.get('role', 'client')})" if 'email' in e else ""
                                             },
                    }

    filter_terms = get_filter_terms_from_request()
    member_id = get_member_id_from_user_context(context)
    entities = get_entities('MemberTable', fields_to_display, filter_terms, partition_key=get_current_app_id(), member_id=member_id)
    return render_member_listing_template(context, 'MemberTable', page, view, page_size, fields_to_display, filter_terms, entities)

def render_member_listing_template(context, entity_name, page, view, page_size, fields_to_display, filter_terms, entities):
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
        entity_add_route=None,
        entities_listing_route=f'/admin/members?entity_table={entity_name}',
        entity_view_route=None,
        entity_action_route=f'/admin/edit?entity_table={entity_name}',
        entity_action_icon='bi-pencil-square',
        entity_action_label='Edit',
        favorite_toggle_route='/favorites/toggle',
        results_target_container=results_target_container,
        context=context
    )


@bp.route('/edit')
@auth.login_required
def edit_entity(context=None):
    table_id = request.args.get('entity_table', None)
    if not table_id:
        return "No table id provided", 404
    entity_instance = get_entity_obj_from_entity_name(table_id)
    
    schema = entity_instance.get_schema()

    composite_key_str = request.args.get('key', None)
    composite_key = eval(composite_key_str) if composite_key_str else None
    es = EntityStore()
    entity_to_edit = es.get_item_by_composite_key(composite_key)
    
    if 'Timestamp' in entity_to_edit:
        del(entity_to_edit['Timestamp'])

    # return json.dumps(entity_to_edit)
    return hx_render_template('admin/admin/entity_editor.html', 
                              entity=entity_to_edit, 
                              schema=schema,
                              table_id=table_id, 
                              errors={},
                              upload_file_url=f'/sys/upload/{table_id}',
                              update_entity_url=f'/admin/update/{table_id}?key={composite_key}',
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
    if partition_field == 'app':
        data['app'] = get_current_app_id()
    elif partition_field:
        if partition_field != 'member_id':
            abort(400, "Only Partition field 'member_id' and 'app' are supported at this time")
            
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
    response=make_response('Item saved successfully.')
    response.headers['HX-Trigger'] = json.dumps({
        "showMessage": { "value" : f"item was saved.", "target": "body" }
    })
    return response
