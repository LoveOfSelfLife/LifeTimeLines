import uuid
from flask import redirect, render_template, request, Blueprint, url_for, session
from auth import auth
from common.blob_store import BlobStore
from common.fitness.active_fitness_registry import get_fitnessclub_entity_names
import os
from hx_common import hx_render_template
from common.fitness.member_info import MembershipRegistry, get_user_info_from_token
from hx_common import FirstTimeUserException, UnregisteredMemberException, is_admin_member, verify_registered_member

bp = Blueprint('/', __name__, template_folder='templates')  

@bp.route("/about")
def about():
    return hx_render_template('about.html', context=None)


@bp.route("/privacy")
def privacy():
    return render_template('privacy.html', context=None)


@bp.route("/data-deletion")
def data_deletion():
    return render_template('data_deletion.html', context=None)


@bp.route("/")
@auth.login_required
def index(context = None):

    user = get_user_info_from_token(context)
    try:
        member = verify_registered_member(user)
        return render_template("base.html", ctx = {"configs" : get_fitnessclub_entity_names(), 
                                                   "user": member.get('name'), 
                                                   "short_name": member.get('short_name'), 
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

@bp.route("/api/upload/<container_name>", methods=["POST"])
@auth.login_required
def api_upload_photo(context, container_name):
    
    user = get_user_info_from_token(context)
    # 1) get the uploaded file
    file = request.files.get("file")
    if not file:
        return "No file uploaded", 400

    # 2) build a unique blob name
    user_id = user['id']  
    ext = os.path.splitext(file.filename)[1]
    blob_name = f"user_{user_id}_{uuid.uuid4().hex}{ext}"

    blob_store = BlobStore(container_name)
    blob_store.upload(file, blob_name)
    blob_client = blob_store.get_blob_client(blob_name)
    public_url = blob_client.url

    return {
        "url": public_url,
        "filename": blob_name,
        "content_type": file.content_type
    }

