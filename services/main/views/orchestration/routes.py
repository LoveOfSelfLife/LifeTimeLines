import os
import json
from flask import Blueprint, render_template, request
import requests

from common.discovery import get_service_url
from common.auth_requestor import AuthRequestor
from common.env_context import Env
from ..common import hx_render_template
from .orchestrations import get_orchestration_definitions, get_orchestration_instances

bp = Blueprint('orchestrations', __name__, template_folder='templates')

@bp.route('/')
def root():
    return hx_render_template('default.html')


@bp.route('/definitions')
def orch_defs():
    definitions = get_orchestration_definitions()
    return hx_render_template('orchestration/orch_definitions.html', definitions=definitions)

@bp.route('/definitions', methods=['POST'])
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

    PRE_URL = get_service_url(service)
    # if os.getenv('ORCH_TESTING_MODE'):
    #     PRE_URL=f'http://localhost:8080'
    # else:
    #     PRE_URL=f'https://{service}.ltl.richkempinski.com'

    URL=f'{PRE_URL}{path}'
    headers={"Authorization": "Bearer " + token,
             "Content-Type": "application/json"}
    print(f'URL:  {URL}')
    context = dict(request.form)
    body = { "id" : definition['id'], "context" : context }
    
    resp = requests.post(URL, data=json.dumps(body), verify=False, headers=headers)
    print(f'response status:  {resp.status_code}')        
    resp.encoding = 'utf-8'        
    instance_id = resp.json().get('instance_id', None)

    execute_cmd = {
    "command": "execute",
    "id": instance_id,
    "arg": 2
    }
    
    path = '/orch/commands'
    URL=f'{PRE_URL}{path}'

    headers={"Authorization": "Bearer " + token,
             "Content-Type": "application/json"}
    print(f'URL:  {URL}')
        
    resp = requests.post(URL, data=json.dumps(execute_cmd), verify=False, headers=headers)
    print(f'response status:  {resp.status_code}')        
    resp.encoding = 'utf-8'        
    exec_cmd_id = resp.json().get('execution_command_id', None)

    return f"Instance ID: {instance_id}, Execution Command ID: {exec_cmd_id}", resp.status_code
    return resp.text, resp.status_code


@bp.route('/definitions/create')
def orch_defs_create():
    def_id = request.args.get('def-id')
    if not def_id:
        return "No definition id provided", 404
    definition = get_orchestration_definitions(def_id)
    orchestration = { "context" : definition['context'] , "definition_id" : definition['id'], "errors": {} }
    return hx_render_template('orchestration/orch_create_instance_form.html', orchestration=orchestration)


@bp.route('/instances')
def orch_instances():
    def_id = request.args.get('def-id')
    definition_id = request.args.get('definition-id')
    def_id = definition_id if definition_id else def_id
    if def_id:
        instances = get_orchestration_instances(def_id)
    else:
        instances = get_orchestration_instances()
    return hx_render_template('orchestration/orch_instances.html', instances=instances, definition_id=def_id if def_id else "")

@bp.route('/instances/<def_id>')
def orch_instances_for_def(def_id):
    instances = get_orchestration_instances(def_id)
    return hx_render_template('orchestration/orch_instances.html', instances=instances, definition_id=def_id)
