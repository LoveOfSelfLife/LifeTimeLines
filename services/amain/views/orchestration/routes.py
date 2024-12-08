from datetime import datetime
import os
import json
from quart import Blueprint, render_template, request, current_app as app
import requests
import logging

from common.auth_requestor import AuthRequestor
from common.env_context import Env
from ..common import hx_render_template
from .orchestrations import get_orchestration_definitions, get_orchestration_instances

bp = Blueprint('orchestrations', __name__, template_folder='templates')
logger = logging.getLogger(__name__)

@bp.route('/')
async def root():
    return await hx_render_template('default.html')


@bp.route('/definitions')
async def orch_defs():
    app.logger.info('applogger: request to orch_defs()')
    logger.info('logger: request to orch_defs()')
    print('print: request to orch_defs()', flush=True)
    with open('/shared/abc.txt', 'w') as f:
        f.write(f'abc, date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    definitions = get_orchestration_definitions()
    return await hx_render_template('orchestration/orch_definitions.html', definitions=definitions)

@bp.route('/definitions', methods=['POST'])
async def post_orch_defs():
    logger.info('request to post_orch_defs()')
    print('request to post_orch_defs()', flush=True)
    def_id = request.args.get('def-id')
    if not def_id:
        return "No definition id provided", 404
    definition = get_orchestration_definitions(def_id)
    scope = [f"api://{Env.AZURE_CLIENT_ID}/.default"]
    auth = AuthRequestor(Env.TENANT_ID, Env.AZURE_CLIENT_ID, Env.AZURE_CLIENT_SECRET, scope)
    token = auth.get_auth_token()

    service = 'otmgr'
    path = '/orchestraions/instances'

    if os.getenv('ORCH_TESTING_MODE'):
        PRE_URL=f'http://localhost:8080'
    else:
        PRE_URL=f'https://{service}.ltl.richkempinski.com'

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
    
    path = '/commands'
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
async def orch_defs_create():
    logger.info('request to orch_defs_create()')
    print('request to orch_defs_create()', flush=True)
    def_id = request.args.get('def-id')
    if not def_id:
        return "No definition id provided", 404
    definition = get_orchestration_definitions(def_id)
    orchestration = { "context" : definition['context'] , "definition_id" : definition['id'], "errors": {} }
    return await hx_render_template('orchestration/orch_create_instance_form.html', orchestration=orchestration)


@bp.route('/instances')
async def orch_instances():
    logger.info('request to orch_instances()')
    print('request to orch_instances()', flush=True)
    def_id = request.args.get('def-id')
    definition_id = request.args.get('definition-id')
    def_id = definition_id if definition_id else def_id
    if def_id:
        instances = get_orchestration_instances(def_id)
    else:
        instances = get_orchestration_instances()
    return await hx_render_template('orchestration/orch_instances.html', instances=instances, definition_id=def_id if def_id else "")

@bp.route('/instances/<def_id>')
async def orch_instances_for_def(def_id):
    logger.info('request to orch_instances_for_def()')
    print('request to orch_instances_for_def()', flush=True)
    instances = get_orchestration_instances(def_id)
    return await hx_render_template('orchestration/orch_instances.html', instances=instances, definition_id=def_id)

@bp.route('/xyz')
async def xyz():
    logger.info('request to xyz()')
    print('request to xyz()', flush=True)
    return "xyz"
