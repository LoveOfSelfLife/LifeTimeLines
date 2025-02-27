from quart import Blueprint, render_template, request
from ..common import hx_render_template
bp = Blueprint('view2', __name__, template_folder='templates')

@bp.route('/')
async def view2_content():
    return await hx_render_template('view2/view2_content.html')
