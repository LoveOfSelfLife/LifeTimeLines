"""
Home Page Routes for the LifeTimeLines application


All routes use HTMX for dynamic updates and follow the existing authentication patterns.
"""

from flask import Blueprint
from auth import auth
from common.template_renderer import hx_render_template
from common.member_entity import get_member_id_from_user_context, get_members_list

bp = Blueprint('home', __name__, template_folder='../../templates')

@bp.route("/")
@auth.login_required  
def home_partial(context=None):
    return home_partial2(context)

def home_partial2(context=None):
    """HTMX partial for home page """
    try:
        
        return hx_render_template(
            template_file='home/dashboard.html',
            context=context
        )
        
    except Exception as e:
        print(f"Error loading home: {e}")
        return hx_render_template(
            template_string='<div class="alert alert-danger">Error loading home</div>',
            context=context
        )

@bp.route("/members")
@auth.login_required  
def about_members(context=None):
    return members_view(context)

def members_view(context=None):
    member_id = get_member_id_from_user_context(context)
    members_list = get_members_list()
    view_type='card'
    return hx_render_template('membership_list.html', members_list=members_list, current_member_id=member_id, view=view_type)
