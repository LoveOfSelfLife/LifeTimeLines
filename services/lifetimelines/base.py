import uuid
from flask import redirect, render_template, request, Blueprint, url_for, session
from auth import auth
import os
from common.app_info import get_current_app_name
from common.fitness.home_page_view import render_finishing_workout_page, render_home_page_workout
from common.member_entity import FirstTimeUserException, MembershipRegistry, UnregisteredMemberException, get_member_detail_from_user_context, get_member_email_from_user_context, get_member_id_from_user_context, get_member_name_from_user_context
from common.template_renderer import hx_render_template

bp = Blueprint('/', __name__, template_folder='templates')  


@bp.route("/privacy")
def privacy():
    return render_template('privacy.html', context=None)


@bp.route("/data-deletion")
def data_deletion():
    return render_template('data_deletion.html', context=None)


@bp.route("/")
@auth.login_required
def index(context = None):
    """Redirect to new home dashboard"""
    member_registry = MembershipRegistry()
    member_registry.refresh_members()   # always refresh members on index page load

    member_id = get_member_id_from_user_context(context)
    member_email = get_member_email_from_user_context(context)
    member_name = get_member_name_from_user_context(context)
    try:
        member = member_registry.verify_member_registration(member_id)

        member_detail = get_member_detail_from_user_context(context)
        
        # current_workout_session_state = get_active_workout_state()
        # if current_workout_session_state:
        #     if current_workout_session_state.get('state', None) == 'workout_started':
        #         # render the workout that is in progress
        #         return render_home_page_workout(member_detail, current_workout_session_state)
        #     elif current_workout_session_state.get('state', None) == 'finishing_workout':
        #         # render the finishing workout screen
        #         return render_finishing_workout_page(member_detail, current_workout_session_state)
        
        # current_program = get_members_current_active_program(member_id)
        # workouts_in_program = []
        
        # if current_program:
        #     # Get all workouts from the program
        #     program_workouts = get_program_workouts(current_program)

        #     # Create alternative workout options
        #     for workout_def in program_workouts:
        #         workout_info = {
        #             'key': str(workout_def.get_composite_key()),
        #             'name': workout_def.get('name', 'Unnamed Workout'),
        #             'description': workout_def.get('description', ''),
        #             'workout_type': workout_def.get('workout_type', 'alternative')
        #         }
        #         workouts_in_program.append(workout_info)
        
        # For the main dashboard, we load the template with placeholders
        # Each section will load its content via HTMX
        return hx_render_template(
            template_file='home/dashboard.html',
            member_id=member_id,
            member=member_detail,
            context=context
        )
        
    except UnregisteredMemberException as e:
        print(f"User not registered: {e}")
        member = member_registry.get_member(member_id)
        app_name = get_current_app_name()
        return render_template("unregistered_member.html",  member=member, app_name=app_name)
    
    except FirstTimeUserException as e:
        print(f"First time user is not registered: {e}")
        member_registry.add_member(member_id, member_email, member_name)
        member = member_registry.get_member(member_id)
        app_name = get_current_app_name()
        return render_template("unregistered_member.html", member=member, app_name=app_name)
    
    except Exception as e:
        print(f"Error loading home dashboard: {e}")
        return hx_render_template(
            template_string='<div class="alert alert-danger">Error loading dashboard</div>',
            context=context
        )    
     
    # try:    
    #     # For the main dashboard, we load the template with placeholders
    #     # Each section will load its content via HTMX
    #     return hx_render_template(
    #         template_string="hello from lifetimelines",
    #         context=context)
        
   
    # except Exception as e:
    #     print(f"Error loading home dashboard: {e}")
    #     return hx_render_template(
    #         template_string='<div class="alert alert-danger">Error loading dashboard</div>',
    #         context=context
    #     )    
    
@bp.route("/logout2")
def logout():
    print("logout")
    session.clear()  # Wipe out user and its token cache from session
    key_list = list(session.keys())
    for key in key_list:
        session.pop(key) 
    
    authority_template = "https://{tenant}.b2clogin.com/{tenant}.onmicrosoft.com/{user_flow}"
    signupsignin_user_flow = os.environ["SIGNUPSIGNIN_USER_FLOW"]
    b2c_tenant = os.environ["B2C_TENANT_NAME"]
    AUTHORITY_URL = authority_template.format(tenant=b2c_tenant, user_flow=signupsignin_user_flow)

    return redirect(  # Also logout from your tenant's web session
        AUTHORITY_URL + "/oauth2/v2.0/logout" + "?post_logout_redirect_uri=" + url_for(".signout_callback", _external=True))

@bp.route("/signout_callback")
def signout_callback():
    print("signout_callback")
    return redirect(url_for(".index"))

