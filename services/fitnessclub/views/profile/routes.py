from flask import Blueprint, render_template, request
from ..common import hx_render_template
bp = Blueprint('profile', __name__, template_folder='templates')
from auth import auth

@bp.route('/')
@auth.login_required
def profile(context=None):
    return hx_render_template('profile.html', context=context)
