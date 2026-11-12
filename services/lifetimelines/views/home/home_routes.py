"""
Home Page Routes for the LifeTimeLines application


All routes use HTMX for dynamic updates and follow the existing authentication patterns.
"""

from common.blueprint import create_blueprint
from common.auth import auth
from common.template_renderer import hx_render_template
from common.member_entity import get_member_id_from_user_context, get_members_list

bp = create_blueprint('home', __name__)

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

