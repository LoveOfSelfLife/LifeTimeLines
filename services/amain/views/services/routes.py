from quart import Blueprint, render_template, request
from ..common import hx_render_template
bp = Blueprint('services', __name__, template_folder='templates')


@bp.route('/')
def root():
    return hx_render_template('default.html')
