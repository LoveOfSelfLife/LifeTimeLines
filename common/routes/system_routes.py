import os
import uuid
from functools import wraps
from common.jwt_auth import requires_auth
from flask import make_response, redirect, render_template, request, session, url_for
import json
from opentelemetry import context
from common.auth import auth
from common.blob_store import BlobStore
from common.blueprint import create_blueprint
from common.member_entity import get_member_id_from_user_context
import logging
import sys
from datetime import datetime
import pytz


class NewYorkFormatter(logging.Formatter):
    _tz = pytz.timezone('America/New_York')

    def formatTime(self, record, datefmt=None):
        return datetime.fromtimestamp(record.created, self._tz).strftime(datefmt or '%Y-%m-%d %H:%M:%S %Z')


_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(NewYorkFormatter('%(asctime)s %(levelname)s:%(name)s:%(message)s'))
logging.basicConfig(level=logging.INFO, handlers=[_handler])
logging.getLogger('azure').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
bp =  create_blueprint('sys', __name__)

ALLOWED_LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")


def _require_admin(context):
    member_id = get_member_id_from_user_context(context)
    if not member_id:
        return make_response({"error": "not authorized"}, 401)
    from common.roles_service import is_member_admin
    if not is_member_admin(member_id):
        logger.warning(f"Non-admin member {member_id} attempted to access log level endpoint")
        return make_response({"error": "admin access required"}, 403)
    return None


@bp.route("/log-level", methods=["GET"])
@auth.login_required
def get_log_level(context=None):
    denied = _require_admin(context)
    if denied:
        return denied
    return {"level": logging.getLevelName(logging.getLogger().getEffectiveLevel())}


@bp.route("/log-level/dialog", methods=["GET"])
@auth.login_required
def log_level_dialog(context=None):
    denied = _require_admin(context)
    if denied:
        return denied
    return render_template('log_level_dialog.html',
                           current_level=logging.getLevelName(logging.getLogger().getEffectiveLevel()),
                           levels=ALLOWED_LOG_LEVELS)


@bp.route("/log-level", methods=["POST"])
@auth.login_required
def set_log_level(context=None):
    denied = _require_admin(context)
    if denied:
        return denied
    payload = request.get_json(silent=True) or {}
    level = payload.get("level") or request.values.get("level") or ""
    level = str(level).strip().upper()
    if level not in ALLOWED_LOG_LEVELS:
        return make_response({"error": f"level must be one of {list(ALLOWED_LOG_LEVELS)}"}, 400)
    logging.getLogger().setLevel(level)
    logging.getLogger('azure').setLevel(max(logging.WARNING, logging.getLevelName(level)))
    logger.warning(f"Log level changed to {level}")
    if request.headers.get("HX-Request"):
        response = make_response('')
        response.headers['HX-Trigger'] = json.dumps(
            {"showMessage": {"value": f"Log level set to {level}", "target": "body"}})
        return response
    return {"level": level}


@bp.route("/logout")
def logout():
    logger.debug("logout")
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


def service_or_user_auth(f):
    """Bearer token (Entra app-only, service-to-service) when an Authorization
    header is present; otherwise the interactive B2C login. The wrapped
    function receives context=None for service callers."""
    user_auth_f = auth.login_required(f)

    @requires_auth
    def service_f():
        return f(context=None)

    @wraps(f)
    def decorated(*args, **kwargs):
        if request.headers.get("Authorization", "").lower().startswith("bearer "):
            return service_f()
        return user_auth_f(*args, **kwargs)
    return decorated


@bp.route("/test-job-run", methods=["POST", "GET"])
@service_or_user_auth
def test_job_run(context):
    if context is None:
        # requires_auth already validated signature, audience and app role
        # include the currrent time in Eastern Time in the log message
        from datetime import datetime
        import pytz
        eastern = pytz.timezone('US/Eastern')
        now_eastern = datetime.now(eastern)
        logger.info(f"Job run triggered by service caller at {now_eastern}")
        response = make_response('{"message": "Job run triggered"}', 200)
        response.headers["Content-Type"] = "application/json"
        return response

    member_id = get_member_id_from_user_context(context)
    if not member_id:
        response = make_response('{"error": "not authorized"}', 401)
        response.headers["Content-Type"] = "application/json"
        logger.warning(f"Unauthorized access attempt to test-job-run by context: {context}")
    else:
        logger.info(f"Job run triggered by member_id: {member_id}")
        response = make_response('{"message": "Job run triggered"}', 200)
        response.headers["Content-Type"] = "application/json"
    return response
