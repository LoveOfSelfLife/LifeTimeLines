from flask import Blueprint, render_template, request
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

@bp.route('/orch-instances')
def orch_instances():
    instances = get_orchestration_instances()
    return hx_render_template('orch_instances.html', instances=instances, definition_id="ALL")

@bp.route('/orch-instances/<def_id>')
def orch_instances_for_def(def_id):
    instances = get_orchestration_instances(def_id)
    return hx_render_template('orch_instances.html', instances=instances, definition_id=def_id)
