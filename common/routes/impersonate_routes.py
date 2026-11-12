
from flask import render_template, request, make_response
from common.blueprint import create_blueprint
from common.auth import auth
from common.impersonation import start_impersonation, stop_impersonation
from common.member_entity import get_members_list, get_impersonated_member_id
import json

bp = create_blueprint('impersonate', __name__)
@bp.route('/')
@auth.login_required
def impersonate_dialog(context=None):
    members = get_members_list()
    current_impersonation_id = get_impersonated_member_id()
    current_impersonated_member = None
    
    if current_impersonation_id:
        current_impersonated_member = next((m for m in members if m.get('id', None) == current_impersonation_id), None)
    
    return render_template('impersonate_dialog.html', 
                         members=members, 
                         current_impersonation=current_impersonation_id,
                         current_impersonated_member=current_impersonated_member)

@bp.route('/start', methods=['POST'])
@auth.login_required
def start_impersonation_route(context=None):
    member_id = request.form.get('member_id')
    if member_id:
        start_impersonation(member_id)
        selected_member = next((m for m in get_members_list() if m.get('id', None) == member_id), None)
        member_name = selected_member.get('name', member_id) if selected_member else member_id
        message = f"Now impersonating {member_name}"
    else:
        message = "Please select a member to impersonate"
    
    response = make_response('')
    response.headers['HX-Trigger'] = json.dumps({
        "showMessage": {"value": message, "target": "body"}
    })
    # Redirect to home page to refresh with new impersonation context
    response.headers['HX-Redirect'] = '/'
    return response

@bp.route('/stop', methods=['POST'])
@auth.login_required
def stop_impersonation_route(context=None):
    stop_impersonation()
    
    response = make_response('')
    response.headers['HX-Trigger'] = json.dumps({
        "showMessage": {"value": "Stopped impersonation", "target": "body"}
    })
    # Redirect to home page to refresh with normal context
    response.headers['HX-Redirect'] = '/'
    return response

