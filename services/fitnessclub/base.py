from flask import redirect, render_template, request, Blueprint, url_for, session
from auth import auth
from common.entities.active_fitness_registry import get_active_fitness_entity_names
import os
bp = Blueprint('/', __name__, template_folder='templates')  

authority_template = "https://{tenant}.b2clogin.com/{tenant}.onmicrosoft.com/{user_flow}"
signupsignin_user_flow = os.environ["SIGNUPSIGNIN_USER_FLOW"] = "1"
b2c_tenant = os.environ["B2C_TENANT_NAME"]
AUTHORITY_URL = authority_template.format(tenant=b2c_tenant, user_flow=signupsignin_user_flow)

@bp.route("/")
@auth.login_required
def index(context = None):
    if context:
        print(f"context: {context}")
    return render_template("base.html", ctx = { "configs" : get_active_fitness_entity_names() })


@bp.route("/logout")
def logout():
    print("logout")
    session.clear()  # Wipe out user and its token cache from session
    key_list = list(session.keys())
    for key in key_list:
        session.pop(key) 
    return redirect(  # Also logout from your tenant's web session
        AUTHORITY_URL + "/oauth2/v2.0/logout" + "?post_logout_redirect_uri=" + url_for("/signout_callback", _external=True))

@bp.route("/signout_callback")
def signout_callback():
    print("signout_callback")
    return redirect(url_for("index"))

