import os
import uuid
from flask import redirect, request, session, url_for
from common.auth import auth
from common.blob_store import BlobStore
from common.blueprint import create_blueprint
from common.member_entity import get_member_id_from_user_context

bp = create_blueprint('sys', __name__) 

@bp.route("/logout")
def logout():
    print("logout")
    session.clear()  # Wipe out user and its token cache from session
    key_list = list(session.keys())
    for key in key_list:
        session.pop(key) 
    
    user_flow = os.environ["SIGNUPSIGNIN_USER_FLOW"]
    tenant = os.environ["B2C_TENANT_NAME"]

    AUTHORITY_URL = f"https://{tenant}.b2clogin.com/{tenant}.onmicrosoft.com/{user_flow}"
     
    return redirect(  # Also logout from your tenant's web session
        AUTHORITY_URL + "/oauth2/v2.0/logout" + "?post_logout_redirect_uri=" + url_for("sys.signout_callback", _external=True))

@bp.route("/signout_callback")
def signout_callback():
    return redirect(url_for("/.index"))

@bp.route("/upload/<container_name>", methods=["POST"])
@auth.login_required
def api_upload_photo(context, container_name):
    
    member_id = get_member_id_from_user_context(context)
    if not member_id:
        return "Unauthorized", 401

    # 1) get the uploaded file
    file = request.files.get("file")
    if not file:
        return "No file uploaded", 400

    # 2) build a unique blob name
    user_id = member_id
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
