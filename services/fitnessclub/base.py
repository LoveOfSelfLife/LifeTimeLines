from flask import redirect, render_template, request, Blueprint, url_for, session
from auth import auth
from services.fitnessclub.active_fitness_registry import get_active_fitness_entity_names
import os

from services.fitnessclub.member_info import MembershipRegistry, get_user_info_from_token
bp = Blueprint('/', __name__, template_folder='templates')  

class FirstTimeUserException(Exception):
    def __init__(self):
        super().__init__("First time user")

class UnregisteredMemberException(Exception):
    def __init__(self):
        super().__init__("Unregistered member")    

class NotAdminMemberException(Exception):
    def __init__(self):
        super().__init__("Not an admin member")

def verify_admin_member(user):
    member = verify_registered_member(user)
    if member.get('level') == 10:
        return member
    else:
        raise NotAdminMemberException()

def verify_registered_member(user):
    members = MembershipRegistry()
    if not members.check_if_member(user['id']):
        raise FirstTimeUserException()
    else:
        user = members.get_member(user['id'])
    if user.get('level') == 0:
        raise UnregisteredMemberException()
    return user

def is_admin_member(user):
    members = MembershipRegistry()
    member = members.get_member(user['id'])
    return member.get('level') == 10    

@bp.route("/")
@auth.login_required
def index(context = None):

    user = get_user_info_from_token(context)
    try:
        member = verify_registered_member(user)
        return render_template("base.html", ctx = {"configs" : get_active_fitness_entity_names(), 
                                                   "user": member.get('name'), 
                                                   "admin": is_admin_member(member) })
        
    except UnregisteredMemberException as e:
        print(f"User not registered: {e}")
        return render_template("unregistered_member.html", ctx = { "user": user.get('name'), "email": user.get('email') })
    
    except FirstTimeUserException as e:
        members = MembershipRegistry()
        members.add_member(user)
        print(f"First time user: {e}")
        return render_template("first_time_user.html", ctx = { "user": user.get('name'), "email": user.get('email') })

@bp.route("/logout")
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
        AUTHORITY_URL + "/oauth2/v2.0/logout" + "?post_logout_redirect_uri=" + url_for("/signout_callback", _external=True))

@bp.route("/signout_callback")
def signout_callback():
    print("signout_callback")
    return redirect(url_for("index"))

