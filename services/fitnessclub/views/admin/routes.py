import os
import json
from flask import Blueprint, jsonify, make_response, render_template, request, redirect
import requests
from auth import auth
from common.fitness.active_fitness_registry import get_fitnessclub_listing_fields_for_entity, get_fitnessclub_entity_type_for_entity, get_fitnessclub_entity_names
from common.env_context import Env
from common.fitness.utils import generate_id
from hx_common import hx_render_template
from common.entity_store import EntityStore
from common.entity_store_cache import EntityStoreCache
bp = Blueprint('admin', __name__, template_folder='templates')

entity_store_cache_dict = {}

def matches_filter(entity,term):
    if term is None:
        return True
    term = term.lower()
    terms = term.split()
    for t in terms:
        for field in entity.get_fields():
            if field in entity and isinstance(entity[field], str):
                if term in entity[field].lower():
                    return True
    return False

def delete_entity(entity):
    entity_store_cache_dict[entity.get_table_name()].delete_item(entity)

def get_list_of_entities(entity_name, filter_term=None):
    global entity_store_cache_dict
    entity_type = get_fitnessclub_entity_type_for_entity(entity_name)

    if entity_store_cache_dict.get(entity_name, None) is None:
        entity_store_cache_dict[entity_name] = EntityStoreCache(entity_type)
    
    entities = entity_store_cache_dict[entity_name].get_items()

    if filter_term:
        return [e for e in entities if matches_filter(e, filter_term)]
    else:
        return entities

def get_filtered_entities(entity_name, filter_term=None):
    
    fields_to_display  = get_fitnessclub_listing_fields_for_entity(entity_name)
    filtered_entities = get_list_of_entities(entity_name, filter_term)

    entities = []
    for e in filtered_entities:
        field_values = [e.get(f, None) for f in fields_to_display]
        key = e.get_composite_key()
        entities.append({"key": key, "field_values": field_values})
    return entities

@bp.route('/')
@auth.login_required
def table_listing(context=None):

    entity_name = request.args.get('entity-table')
    filter_term = request.args.get('filter', '')
    page = int(request.args.get('page', 1))

    page_size = 10

    entities = get_filtered_entities(entity_name, filter_term)

    total_pages = (len(entities) + page_size - 1) // page_size
    start = (page - 1) * page_size
    end = start + page_size
    current = entities[start:end]

    if not entity_name:
        return "No entity name provided", 404
    entity_type = get_fitnessclub_entity_type_for_entity(entity_name)
    fields_to_display  = get_fitnessclub_listing_fields_for_entity(entity_name)

    return hx_render_template('admin/entity_list.html', 
                              fields_to_display=fields_to_display,
                              entities=current,
                              entity_name=entity_name,
                              entity_display_name=entity_type.get_display_name(),
                              filter_term=filter_term,
                              page=page,
                              total_pages=total_pages,
                              context=context) 

@bp.route('/entities-listing')
def entities_fragment():
    entity_name = request.args.get('entity-table')    
    filter_term = request.args.get('filter', '')
    page = int(request.args.get('page', 1))

    page_size = 10

    fields_to_display  = get_fitnessclub_listing_fields_for_entity(entity_name)

    entities = get_filtered_entities(entity_name, filter_term)

    total_pages = (len(entities) + page_size - 1) // page_size
    start = (page - 1) * page_size
    end = start + page_size
    current = entities[start:end]

    return render_template(
        "entity_list_fragment.html",
        entity_name=entity_name,
        fields_to_display=fields_to_display,
        entities=current,
        filter_term=filter_term,
        page=page,
        total_pages=total_pages
    )

@bp.route('/edit')
@auth.login_required
def edit_entity(context=None):
    table_id = request.args.get('entity-table', None)
    if not table_id:
        return "No table id provided", 404
    if table_id not in get_fitnessclub_entity_names():
        return "Table not allowed", 404
    entity_instance = get_fitnessclub_entity_type_for_entity(table_id)
    
    schema = entity_instance.get_schema()

    composite_key_str = request.args.get('key', None)
    composite_key = eval(composite_key_str) if composite_key_str else None
    es = EntityStore()
    entity_to_edit = es.get_item_by_composite_key(entity_instance, composite_key)
    
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

@bp.route('/delete/<table_id>', methods=['POST'])
@auth.login_required
def delete_entity_from_table(context=None, table_id=None):
    if not table_id:
        return "No table id provided", 404
    if table_id not in get_fitnessclub_entity_names():
        return "Table not allowed", 404
    entity = get_fitnessclub_entity_type_for_entity(table_id)    


    schema = entity.get_schema()

    composite_key_str = request.args.get('key', None)
    composite_key = eval(composite_key_str) if composite_key_str else None

    es = EntityStore()
    entity_to_delete = es.get_item_by_composite_key(entity, composite_key)
    
    if not entity_to_delete:
        return "Entity not found", 404

    delete_entity(entity_to_delete)
    # es.delete_items([entity_to_delete])

    response = make_response('')
    response.headers['HX-Trigger'] = json.dumps({
        "eventListChanged": None,
        "showMessage": f"selected item was deleted."
    })
    # return response
    return redirect(f'/admin?entity-table={table_id}', 302, response)

@bp.route('/add/<table_id>', methods=['GET'])
@auth.login_required
def existing_entity_editor(context=None, table_id=None):
    if not table_id:
        return "No table id provided", 404
    if table_id not in get_fitnessclub_entity_names():
        return "Table not allowed", 404
    entity = get_fitnessclub_entity_type_for_entity(table_id)
    es = EntityStore()
    entity_to_edit = {}
    schema = entity.get_schema()

    return hx_render_template('admin/entity_editor.html', 
                            entity=entity_to_edit, 
                            schema=schema,
                            table_id=table_id, 
                            errors={},
                            upload_file_url=f'/api/upload/{table_id}',
                            update_entity_url=f'/admin/update/{table_id}',
                            delete_entity_url=f'/admin/delete/{table_id}?key={entity_to_edit.get("id")}&partition={entity_to_edit.get("partition_value")}',
                            context=context)
        
@bp.route('/update/<table_id>', methods=['POST'])
@auth.login_required
def update_entity_save_json(context=None, table_id=None):

    # 1) Parse the incoming JSON
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Invalid or missing JSON"}), 400

    print(f"Received JSON payload for table {table_id}: {data}")
    entity = get_fitnessclub_entity_type_for_entity(table_id)        

    es = EntityStore()
    
    # this assumes that the entity uses 'id' as the key field
    # it also assumes that the entity has a fixed partition value
    # probably need to make this more generic in the future
    # TODO: fix this to be more generic

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
        "showMessage": f"item was saved."
    })
    response.headers['HX-Redirect'] = f'/admin?entity-table={table_id}'
    return response
    # return redirect(f'/admin?entity-table={table_id}', 302, response)
    # return redirect(f'/', 302, response)
