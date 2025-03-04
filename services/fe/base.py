from flask import redirect, render_template, request, Blueprint, url_for
from auth import auth
from common.entities.active_fitness_registry import get_active_fitness_entity_names
bp = Blueprint('/', __name__, template_folder='templates')  

@bp.route("/")
@auth.login_required
def index(context = None):
    if context:
        print(f"context: {context}")
    return render_template("base.html", ctx = { "configs" : get_active_fitness_entity_names() })
