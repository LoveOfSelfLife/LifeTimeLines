from flask import Blueprint, redirect, render_template, request, url_for
from hx_common import hx_render_template
from common.fitness.member_entity import get_user_info_from_token, get_user_profile, save_user_profile
bp = Blueprint('profile', __name__, template_folder='templates')
from auth import auth

@bp.route('/')
@auth.login_required
def profile(context=None):
    profile = {
        "id": "123456",
        "name": "John Doe",
        "shortname": "JD",
        "email": "jd@mail.com",
        "mobile": "123-456-7890",
        "sms_consent": "agree" }
    
    id = get_user_info_from_token(context).get('id')

    profile = get_user_profile(id)

    return hx_render_template('profile_nav.html', 
                              context=context, 
                              profile=profile,
                              hx_push_url="/profile/update",
                              update_url="/profile/update")
@bp.route('/profile2')
@auth.login_required
def profile2(context=None):
    profile = {
        "id": "123456",
        "name": "John Doe",
        "shortname": "JD",
        "email": "jd@mail.com",
        "mobile": "123-456-7890",
        "sms_consent": "agree" }
    
    id = get_user_info_from_token(context).get('id')

    profile = get_user_profile(id)

    return hx_render_template('profile2.html', 
                              context=context, 
                              profile=profile,
                              hx_push_url="/profile/update",
                              update_url="/profile/update")

@bp.route('/settings')
@auth.login_required
def settings(context=None):

    return hx_render_template('settings.html', 
                              context=context, 
                              profile=profile,
                              hx_push_url="/profile/update",
                              update_url="/profile/update")

@bp.route('/update', methods=['POST'])
@auth.login_required
def update_profile(context=None):
    print(f"Request: {request.form}")

    profile = save_user_profile(request.form, 
                                request.files)
    return redirect("/")
  
