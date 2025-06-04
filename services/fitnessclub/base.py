import uuid
from flask import redirect, render_template, request, Blueprint, url_for, session
from auth import auth
from common.blob_store import BlobStore
import os
from common.fitness.hx_common import hx_render_template
from common.fitness.member_entity import MembershipRegistry, get_member_detail_from_user_context
from common.fitness.hx_common import FirstTimeUserException, UnregisteredMemberException, is_admin_member, verify_member_registration
from common.fitness.home_page_view import generate_current_home_page_view

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

@bp.route("/home")
def home():
    return redirect("/")

@bp.route("/")
@auth.login_required
def index(context = None):
    member_registry = MembershipRegistry()
    member_registry.refresh_members()   # always refresh members on index page load

    user = get_member_detail_from_user_context(context)
    try:
        member = verify_member_registration(user)
        home_page_view = generate_current_home_page_view(member)
        return hx_render_template(template_string=home_page_view, context=context, member=member)
        
    except UnregisteredMemberException as e:
        print(f"User not registered: {e}")
        member = member_registry.get_member(user['id'])
        return render_template("unregistered_member.html",  member=member)
    
    except FirstTimeUserException as e:
        print(f"First time user exception: {e}")
        member_registry.add_member(user)
        member = member_registry.get_member(user['id'])
        return render_template("first_time_user.html", member=member)

    

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
    
    user = get_member_detail_from_user_context(context)
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

