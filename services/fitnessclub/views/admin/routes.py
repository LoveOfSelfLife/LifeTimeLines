import os
import json
from flask import Blueprint, jsonify, render_template, request, redirect
import requests
from auth import auth
from common.fitness.active_fitness_registry import get_fitnessclub_entity_names, get_fitnessclub_entity_by_name
from common.env_context import Env
from hx_common import hx_render_template
from common.entity_store import EntityStore
bp = Blueprint('admin', __name__, template_folder='templates')

def get_entity_table_ctx(config):
    entity, listing_fields  =get_fitnessclub_entity_by_name(config)
    fields = entity.get_fields()
    es = EntityStore()
    entities_list = es.list_items(entity)
    entities = []
    for e in entities_list:
        val_list = []
        for f in listing_fields:
            v = e.get(f, None)
            val_list.append(v)
        key_val = e.get_key_value()
        partition_val = e.get_partition_value()
        entities.append({"key_val": key_val, "partition_val": partition_val, "val_list": val_list})

    ctx = {
            "entity_type" : config,
            "fields" : listing_fields,
            "entities" : entities }
    return ctx
    
def get_editable_fields(entity):
    kf = entity.get_key_field()
    pf = entity.get_partition_field()
    efields = []
    for k in entity.get_fields():
        if k in [kf, pf, 'Timestamp']:
            continue
        efields.append(k)
    return efields

def get_allowed_tables():
    return get_fitnessclub_entity_names()

@bp.route('/')
@auth.login_required
def table_listing(context=None):

    table_id = request.args.get('entity-type')
    if not table_id:
        return "No table name provided", 404

    ctx = get_entity_table_ctx(table_id)

    return hx_render_template('admin/entity_list.html', 
                              ctx=ctx, table_id=table_id, 
                              context=context) 

@bp.route('/edit')
@auth.login_required
def entity_editor(context=None):
    table_id = request.args.get('entity-type')
    if not table_id:
        return "No table id provided", 404
    if table_id not in get_allowed_tables():
        return "Table not allowed", 404
    entity, _ = get_fitnessclub_entity_by_name(table_id)

    key_val = request.args.get('key', None)
    partition_val = request.args.get('partition', None)
    es = EntityStore()
    kf = entity.get_key_field()
    pf = entity.get_partition_field()
    entity[kf] = key_val
    if pf and partition_val:
        entity[pf] = partition_val
    entity_to_edit = es.get_item(entity)
    fields = get_editable_fields(entity)
    schema = entity.get_schema()
    if 'Timestamp' in entity_to_edit:
        del(entity_to_edit['Timestamp'])

    # return json.dumps(entity_to_edit)
    return hx_render_template('admin/entity_editor.html', entity=entity_to_edit, schema=schema,
                              fields=fields, 
                              table_id=table_id, errors={},
                              key_val = key_val, partition_val = partition_val,
                              back_url = f'/admin?entity-type={table_id}',
                              update_url=f'/admin/update?entity-type={table_id}&key={key_val}&partition={partition_val}',
                              context=context)
    
@bp.route('/update', methods=['POST'])
@auth.login_required
def update_entity(context=None):
    table_id = request.args.get('entity-type')
    if not table_id:
        return "No table id provided", 404
    if table_id not in get_allowed_tables():
        return "Table not allowed", 404
    entity_type, _ = get_fitnessclub_entity_by_name(table_id)
    key_val = request.args.get('key', None)
    partition_val = request.args.get('partition', None)
    entity = request.form
    es = EntityStore()
    
    updated_entity = entity_type
    updated_entity.initialize(entity)

    kf = updated_entity.get_key_field()
    pf = updated_entity.get_partition_field()
    updated_entity[kf] = key_val
    if pf and partition_val:
        updated_entity[pf] = partition_val    

    print(f"updated_entity: {updated_entity}")

    es.upsert_item(updated_entity)
    return redirect(f'/admin?entity-type={table_id}') 

@bp.route('/save/<table_id>', methods=['POST'])
@auth.login_required
def save_json(context=None, table_id=None):

    # 1) Parse the incoming JSON
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Invalid or missing JSON"}), 400

    # 2) Here’s where you’d persist it:
    #    e.g. save_to_db(data), write to file, etc.
    #    For now we'll just log it

    print(f"Received JSON payload for table {table_id}: {data}")
    entity,_ = get_fitnessclub_entity_by_name(table_id)
    es = EntityStore()
    entity.initialize(data)
    es.upsert_item(entity)

    # 3) Send back a JSON confirmation
    return jsonify({
        "status": "success",
        "message": "JSON saved",
        # echoing back the payload is optional:
        # "savedData": data
    }), 200
