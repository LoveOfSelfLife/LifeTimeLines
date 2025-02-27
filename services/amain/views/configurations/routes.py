import os
import json
from quart import Blueprint, render_template, request, redirect
import requests

from common.entities.entity_registry import get_editable_entity_names
from common.env_context import Env
from common.entities.entity_registry import get_editable_entity_by_name
from ..common import hx_render_template
from common.entity_store import EntityStore
bp = Blueprint('configurations', __name__, template_folder='templates')

def get_config_entity_ctx(config):
    entity =get_editable_entity_by_name(config)
    fields = entity.get_fields()
    es = EntityStore()
    entities_list = es.list_items(entity)
    entities = []
    for e in entities_list:
        val_list = []
        for f in fields:
            v = e.get(f, None)
            val_list.append(v)
        key_val = e.get_key_value()
        partition_val = e.get_partition_value()
        entities.append({"key_val": key_val, "partition_val": partition_val, "val_list": val_list})

    ctx = {
            "entity_type" : config,
            "fields" : fields,
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
    return get_editable_entity_names()

@bp.route('/')
async def config_listing():

    config_id = request.args.get('entity-type')
    if not config_id:
        return "No config provided", 404

    ctx = get_config_entity_ctx(config_id)

    return await hx_render_template('configurations/entity_list.html', ctx=ctx, table_id=config_id) 


@bp.route('/edit')
async def orch_defs_create():
    table_id = request.args.get('entity-type')
    if not table_id:
        return "No table id provided", 404
    if table_id not in get_allowed_tables():
        return "Table not allowed", 404
    entity = get_editable_entity_by_name(table_id)
    # entity = get_config_entity_type(table_id)
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
    
    # return json.dumps(entity_to_edit)
    return await hx_render_template('configurations/entity_edit.html', entity=entity_to_edit, fields=fields, 
                              table_id=table_id, errors={},
                              key_val = key_val, partition_val = partition_val,
                              back_url = f'/configurations?entity-type={table_id}',
                              update_url=f'/configurations/update?entity-type={table_id}&key={key_val}&partition={partition_val}')
    
@bp.route('/update', methods=['POST'])
async def update_entity():
    table_id = request.args.get('entity-type')
    if not table_id:
        return "No table id provided", 404
    if table_id not in get_allowed_tables():
        return "Table not allowed", 404
    entity_type = get_editable_entity_by_name(table_id)
    # entity_type = get_config_entity_type(table_id)
    key_val = request.args.get('key', None)
    partition_val = request.args.get('partition', None)
    entity = await request.form
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
    return redirect(f'/configurations?entity-type={table_id}') 
