import uuid
from flask import redirect, render_template, request, Blueprint, url_for, session
from auth import auth
import os
from common.fitness.home_page_view import render_finishing_workout_page, render_home_page_workout
from common.simple_hx_common import hx_render_template

bp = Blueprint('/', __name__, template_folder='templates')  


@bp.route("/privacy")
def privacy():
    return render_template('privacy.html', context=None)


@bp.route("/data-deletion")
def data_deletion():
    return render_template('data_deletion.html', context=None)


@bp.route("/")
@auth.login_required
def index(context = None):
    """Redirect to new home dashboard"""
 
    try:    
        # For the main dashboard, we load the template with placeholders
        # Each section will load its content via HTMX
        return hx_render_template(
            template_string="hello from lifetimelines",
            context=context)
        
   
    except Exception as e:
        print(f"Error loading home dashboard: {e}")
        return hx_render_template(
            template_string='<div class="alert alert-danger">Error loading dashboard</div>',
            context=context
        )    
    
@bp.route("/logout2")
def logout():
    print("logout")
    session.clear()  # Wipe out user and its token cache from session
    key_list = list(session.keys())
    for key in key_list:
        session.pop(key) 
    
    authority_template = "https://{tenant}.b2clogin.com/{tenant}.onmicrosoft.com/{user_flow}"
    signupsignin_user_flow = os.environ["SIGNUPSIGNIN_USER_FLOW"] = "1"
    b2c_tenant = os.environ["B2C_TENANT_NAME"]
    AUTHORITY_URL = authority_template.format(tenant=b2c_tenant, user_flow=signupsignin_user_flow)

    return redirect(  # Also logout from your tenant's web session
        AUTHORITY_URL + "/oauth2/v2.0/logout" + "?post_logout_redirect_uri=" + url_for(".signout_callback", _external=True))

@bp.route("/signout_callback")
def signout_callback():
    print("signout_callback")
    return redirect(url_for("index"))

