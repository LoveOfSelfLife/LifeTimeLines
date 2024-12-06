from quart import redirect, render_template, request, Blueprint

# from services.main.views.configurations.extra import get_editable_entity_names
from common.entities.entity_registry import get_editable_entity_names
bp = Blueprint('', __name__, template_folder='templates')  

@bp.route("/")
async def index():
    return await render_template("base.html", ctx = { "configs" : get_editable_entity_names() })
