import uuid
from flask import redirect, render_template, request, url_for, session
from common.blueprint import create_blueprint
from common.auth import auth
from common.blob_store import BlobStore
import os
from common.fitness.home_page_view import render_finishing_workout_page, render_home_page_workout
from common.template_renderer import hx_render_template
from common.member_entity import MembershipRegistry, get_member_detail_from_user_context, get_member_email_from_user_context, get_member_id_from_user_context, get_member_name_from_user_context, FirstTimeUserException, UnregisteredMemberException
from common.fitness.programs import get_members_current_active_program, get_program_workouts
from common.fitness.workout_state import get_active_workout_state

bp = create_blueprint('/', __name__)  

@bp.route("/about")
def about():
    return hx_render_template('about.html', context=None)


@bp.route("/privacy")
def privacy():
    return hx_render_template('privacy.html', context=None)


@bp.route("/data-deletion")
def data_deletion():
    return hx_render_template('data_deletion.html', context=None)

@bp.route("/home")
def home():
    return redirect("/")

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
        
        current_workout_session_state = get_active_workout_state()
        if current_workout_session_state:
            if current_workout_session_state.get('state', None) == 'workout_started':
                # render the workout that is in progress
                return render_home_page_workout(member_detail, current_workout_session_state)
            elif current_workout_session_state.get('state', None) == 'finishing_workout':
                # render the finishing workout screen
                return render_finishing_workout_page(member_detail, current_workout_session_state)
        
        current_program = get_members_current_active_program(member_id)
        workouts_in_program = []
        
        if current_program:
            # Get all workouts from the program
            program_workouts = get_program_workouts(current_program)

            # Create alternative workout options
            for workout_def in program_workouts:
                workout_info = {
                    'key': str(workout_def.get_composite_key()),
                    'name': workout_def.get('name', 'Unnamed Workout'),
                    'description': workout_def.get('description', ''),
                    'workout_type': workout_def.get('workout_type', 'alternative')
                }
                workouts_in_program.append(workout_info)
        
        # For the main dashboard, we load the template with placeholders
        # Each section will load its content via HTMX
        return hx_render_template(
            template_file='home/dashboard.html',
            member=member_detail,
            workouts_in_program=workouts_in_program,
            context=context,
            program_key=current_program.get_composite_key() if current_program else None
        )
        
    except UnregisteredMemberException as e:
        print(f"User not registered: {e}")
        # user is in the registry, but they have not yet been approved
        member = member_registry.get_member(member_id)
        return render_template("unregistered_member.html",  member=member)
    
    except FirstTimeUserException as e:
        print(f"First time user exception: {e}")
        # the member was not previously registered, so we add them to the registry here
        # TODO: consider sending a notification to the admins about the newly registered member, for approval
        member_registry.add_member(member_id, member_email, member_name)
        member = member_registry.get_member(member_id)
        return render_template("unregistered_member.html", member=member)
    
    except Exception as e:
        print(f"Error loading home dashboard: {e}")
        return hx_render_template(
            template_string='<div class="alert alert-danger">Error loading dashboard</div>',
            context=context
        )    
    
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

