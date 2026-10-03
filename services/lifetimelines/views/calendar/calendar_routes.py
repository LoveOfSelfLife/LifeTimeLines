"""
Calendar Page Routes for the LifeTimeLines application


All routes use HTMX for dynamic updates and follow the existing authentication patterns.
"""

from common.blueprint import create_blueprint
from auth import auth
from common.template_renderer import hx_render_template

# bp = Blueprint('calendar', __name__, template_folder='../../templates')
bp = create_blueprint('calendar', __name__)

@bp.route("/")
@auth.login_required  
def calendar_partial(context=None):
    return calendar_partial2(context)

def calendar_partial2(context=None):
    """HTMX partial for calendar page """
    try:
        
        return hx_render_template(
            template_file='calendar/calendar.html',
            context=context
        )
        
    except Exception as e:
        print(f"Error loading calendar: {e}")
        return hx_render_template(
            template_string='<div class="alert alert-danger">Error loading calendar</div>',
            context=context
        )
