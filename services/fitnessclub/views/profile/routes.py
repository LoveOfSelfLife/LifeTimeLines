from flask import Blueprint, render_template, request
from hx_common import hx_render_template
from member_info import get_user_info_from_token, get_user_profile, save_user_profile
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

    return hx_render_template('profile.html', 
                              context=context, 
                              profile=profile,
                              update_url="/profile/update")

@bp.route('/update', methods=['POST'])
@auth.login_required
def update_profile(context=None):
    print(f"Request: {request.form}")

    profile = save_user_profile(request.form)
    return hx_render_template('profile.html', 
                              context=context, 
                              profile=profile,
                              update_url="/profile/update")


    
