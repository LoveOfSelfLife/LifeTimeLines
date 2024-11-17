import json
from flask import Blueprint, render_template, request
import requests

from common.auth_requestor import AuthRequestor
from common.env_context import Env
from ..common import hx_render_template
from .orchestrations import get_orchestration_definitions, get_orchestration_instances

bp = Blueprint('tables', __name__, template_folder='templates')


@bp.route('/')
def root():
    return hx_render_template('default.html')

@bp.route('/orch-defs')
def orch_defs():
    definitions = get_orchestration_definitions()
    return hx_render_template('orch_definitions.html', definitions=definitions)

@bp.route('/orch-defs', methods=['POST'])
def post_orch_defs():
    def_id = request.args.get('def-id')
    if not def_id:
        return "No definition id provided", 404
    definition = get_orchestration_definitions(def_id)
    scope = [f"api://{Env.AZURE_CLIENT_ID}/.default"]
    auth = AuthRequestor(Env.TENANT_ID, Env.AZURE_CLIENT_ID, Env.AZURE_CLIENT_SECRET, scope)
    token = auth.get_auth_token()

    service = 'otmgr'
    path = '/orch/instances'
    URL=f'https://{service}.ltl.richkempinski.com{path}'
    headers={'Authorization': 'Bearer ' + token}
    print(f'URL:  {URL}')
    body = { "id" : definition['id'], "context" : request.form }
    resp = requests.post(URL, data=body, verify=False, headers=headers)
    print(f'response status:  {resp.status_code}')        
    resp.encoding = 'utf-8'        
    instance_id = resp.json().get('instance_id', None)
    return resp.text, resp.status_code

    return json.dumps(definition, indent=4)
    # return hx_render_template('orch_definitions.html', definitions=definitions)

@bp.route('/orch-defs/create')
def orch_defs_create():
    def_id = request.args.get('def-id')
    if not def_id:
        return "No definition id provided", 404
    definition = get_orchestration_definitions(def_id)
    orchestration = { "context" : definition['context'] , "definition_id" : definition['id'], "errors": {} }
    return hx_render_template('orch_create_instance_form.html', orchestration=orchestration)


@bp.route('/orch-instances')
def orch_instances():
    def_if = request.args.get('def-id')
    if def_if:
        instances = get_orchestration_instances(def_if)
    else:
        instances = get_orchestration_instances()
    return hx_render_template('orch_instances.html', instances=instances, definition_id=def_if if def_if else "")

@bp.route('/orch-instances/<def_id>')
def orch_instances_for_def(def_id):
    instances = get_orchestration_instances(def_id)
    return hx_render_template('orch_instances.html', instances=instances, definition_id=def_id)
