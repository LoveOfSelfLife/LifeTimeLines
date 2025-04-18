from flask import Blueprint, render_template, request
from hx_common import hx_render_template
bp = Blueprint('exercises', __name__, template_folder='templates')
from auth import auth

@bp.route('/')
@auth.login_required
def root(context=None):
    return hx_render_template('exercises.html', context=context)
