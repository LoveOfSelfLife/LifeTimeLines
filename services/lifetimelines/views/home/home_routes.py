"""
Home Page Routes for the LifeTimeLines application


All routes use HTMX for dynamic updates and follow the existing authentication patterns.
"""

from flask import Blueprint, abort, make_response, render_template, request, jsonify, session, redirect, url_for
from auth import auth
from common.template_renderer import hx_render_template
from datetime import datetime, timezone, date
import json

bp = Blueprint('home', __name__, template_folder='../../templates')

@bp.route("/")
@auth.login_required  
def home_partial(context=None):
    return home_partial2(context)

def home_partial2(context=None):
    """HTMX partial for home page """
    try:
        
        return hx_render_template(
            template_file='home/home.html',
            context=context
        )
        
    except Exception as e:
        print(f"Error loading home: {e}")
        return hx_render_template(
            template_string='<div class="alert alert-danger">Error loading home</div>',
            context=context
        )

