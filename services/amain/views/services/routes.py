from quart import Blueprint, render_template, request
from ..common import hx_render_template
bp = Blueprint('services', __name__, template_folder='templates')


@bp.route('/')
async def root():
    return await hx_render_template('default.html')

@bp.route('/test')
async def root():
    return await hx_render_template('services.html')


