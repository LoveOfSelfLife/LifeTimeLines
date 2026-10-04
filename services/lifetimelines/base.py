import uuid
from flask import redirect, render_template, request, Blueprint, url_for, session
from common.auth import auth
import os
from common.app_info import get_current_app_name
from common.blob_store import BlobStore
from common.fitness.home_page_view import render_finishing_workout_page, render_home_page_workout
from common.template_renderer import hx_render_template
from common.member_entity import FirstTimeUserException, MembershipRegistry, UnregisteredMemberException, get_member_detail_from_user_context, get_member_email_from_user_context, get_member_id_from_user_context, get_member_name_from_user_context
from common.template_renderer import hx_render_template

bp = Blueprint('/', __name__, template_folder='templates')  

@bp.route("/")
@auth.login_required
def index(context = None):
    """Redirect to new home dashboard"""
    MembershipRegistry().refresh_members()   # always refresh members on index page load

    member_id = get_member_id_from_user_context(context)
    member_detail = get_member_detail_from_user_context(context)
        
    return hx_render_template(
        template_file='home/dashboard.html',
        member_id=member_id,
        member=member_detail,
        context=context
        )
     

@bp.route("/about")
def about():
    return hx_render_template('static_info/about.html', context=None)

@bp.route("/privacy")
def privacy():
    return hx_render_template('static_info/privacy.html', context=None)

@bp.route("/data-deletion")
def data_deletion():
    return hx_render_template('static_info/data_deletion.html', context=None)

