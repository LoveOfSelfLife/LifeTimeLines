from flask import Blueprint, render_template, request
from ..common import hx_render_template
bp = Blueprint('processes', __name__, template_folder='templates')


@bp.route('/')
def root():
    return hx_render_template('default.html')
