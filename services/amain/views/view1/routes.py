from quart import Blueprint, render_template, request
from ..common import hx_render_template
bp = Blueprint('view1', __name__, template_folder='templates')

@bp.route('/')
def view1_content():
    return hx_render_template('view1/view1_content.html')
    
@bp.route('/list')
def view1_list():
    return hx_render_template('view1/entity_list.html')

