"""
Admin Page Routes for the LifeTimeLines application


All routes use HTMX for dynamic updates and follow the existing authentication patterns.
"""

from flask import Blueprint, json, make_response, render_template, request, request, session
from auth import auth
from common.impersonation import get_impersonated_member_id, start_impersonation, stop_impersonation
from common.member_entity import get_members_list
from common.template_renderer import hx_render_template

bp = Blueprint('admin', __name__, template_folder='templates')

@bp.route("/")
@auth.login_required  
def admin_partial(context=None):
    return admin_partial2(context)

def admin_partial2(context=None):
    """HTMX partial for admin page """
    try:
        
        return hx_render_template(
            template_file='admin/admin.html',
            context=context
        )
        
    except Exception as e:
        print(f"Error loading admin page: {e}")
        return hx_render_template(
            template_string='<div class="alert alert-danger">Error loading admin page</div>',
            context=context
        )

@bp.route('/members')
@auth.login_required
def members(context=None):
    return members_listing(context=context)

def members_listing(context=None):
    pass
    return hx_render_template(
        template_string='<div class="alert ">under construction</div>',
        context=context
    )
    # page = int(request.args.get('page', 1))
    # page_size = 100

    # # Handle view preference
    # view = (request.form.get('view') if request.method == 'POST' 
    #         else request.args.get('view')) or session.get('view_preference', 'list')
    
    # if view != session.get('view_preference'):
    #     session['view_preference'] = view
    
    # fields_to_display = get_fitnessclub_listing_fields_for_entity('MemberTable')
    # filter_terms = get_filter_terms_from_request()

    # member_id = get_member_id_from_user_context(context)

    # entities = get_entities('MemberTable', fields_to_display, filter_terms, partition_key=get_current_app_id(), member_id=member_id)
    # return render_entity_template(context, 'MemberTable', page, view, page_size, fields_to_display, filter_terms, entities)


@bp.route('/impersonate')
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

@bp.route('/start_impersonation', methods=['POST'])
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

@bp.route('/stop_impersonation', methods=['POST'])
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
