import uuid
from flask import redirect, render_template, request, Blueprint, url_for, session
from auth import auth
from common.blob_store import BlobStore
import os
from common.fitness.home_page_view import render_finishing_workout_page, render_home_page_workout
from common.fitness.hx_common import hx_render_template
from common.fitness.member_entity import MembershipRegistry, get_member_detail_from_user_context, get_member_email_from_user_context, get_member_id_from_user_context, get_member_name_from_user_context, FirstTimeUserException, UnregisteredMemberException
from common.fitness.programs import get_members_current_active_program, get_program_workouts
from common.fitness.workout_state import get_active_workout_state

bp = Blueprint('/', __name__, template_folder='templates')  

@bp.route("/about")
def about():
    return hx_render_template('about.html', context=None)

@bp.route("/get-edit-form/<item_id>")
def get_edit_form(item_id, context=None):
    new_text = request.args.get("new_text", "Click me (or hold 1s) to edit")
    return f"""
            <!-- The editable form (returned by server) -->
            <form id="text-container" hx-put="/save-data/{item_id}" 
                hx-target="#text-container" 
                hx-swap="outerHTML" 
                hx-trigger="focusout">
                <input type="text" 
                    name="new_text" 
                    value="{new_text}" 
                    onfocus="this.select()"
                    autofocus>
            </form>
            """

@bp.route("/save-data/<item_id>", methods=["PUT"])
def save_data(item_id, context=None):
    new_text = request.form.get("new_text", "")
    # Here you would typically save the new text to your database
    print(f"Saving new text for item {item_id}: {new_text}")
    # Return the updated content to replace the form
    return f'<div id="text-container" hx-get="/get-edit-form/{item_id}?new_text={new_text}" hx-target="#text-container" hx-trigger="dblclick, mousedown delay:1s" hx-swap="outerHTML">{new_text}</div>'


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
    """Redirect to new home dashboard"""
    member_registry = MembershipRegistry()
    member_registry.refresh_members()   # always refresh members on index page load

    member_id = get_member_id_from_user_context(context)
    member_email = get_member_email_from_user_context(context)
    member_name = get_member_name_from_user_context(context)
    try:
        member = member_registry.verify_member_registration(member_id)

        member_detail = get_member_detail_from_user_context(context)
        
        current_state = get_active_workout_state()
        if current_state:
            if current_state.get('state', None) == 'workout_started':
                # render the workout that is in progress
                return render_home_page_workout(member_detail, current_state)
            elif current_state.get('state', None) == 'finishing_workout':
                # render the finishing workout screen
                return render_finishing_workout_page(member_detail, current_state)
        
        current_program = get_members_current_active_program(member_id)
        workouts_in_program = []
        
        if current_program:
            # Get all workouts from the program
            program_workouts = get_program_workouts(current_program, member_id)

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
        member = member_registry.get_member(member_id)
        return render_template("unregistered_member.html",  member=member)
    
    except FirstTimeUserException as e:
        print(f"First time user exception: {e}")
        member_registry.add_member(member_id, member_email, member_name)
        member = member_registry.get_member(member_id)
        return render_template("first_time_user.html", member=member)
    
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
    signupsignin_user_flow = os.environ["SIGNUPSIGNIN_USER_FLOW"] = "1"
    b2c_tenant = os.environ["B2C_TENANT_NAME"]
    AUTHORITY_URL = authority_template.format(tenant=b2c_tenant, user_flow=signupsignin_user_flow)

    return redirect(  # Also logout from your tenant's web session
        AUTHORITY_URL + "/oauth2/v2.0/logout" + "?post_logout_redirect_uri=" + url_for(".signout_callback", _external=True))

@bp.route("/signout_callback")
def signout_callback():
    print("signout_callback")
    return redirect(url_for("index"))

@bp.route("/api/upload/<container_name>", methods=["POST"])
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

# Team selection and members routes

@bp.route("/teams/select", methods=["POST"])
@auth.login_required
def select_team(context=None):
    """Allow coaches to select their active team"""
    from common.fitness.roles_service import set_primary_team_id_for_context, get_member_role, get_teams_managed_by_coach
    import json
    from flask import make_response
    
    team_id = request.form.get('team_id')
    member_id = get_member_id_from_user_context(context)
    
    if not team_id:
        return "Team ID required", 400
    
    # Verify user is a coach and has access to this team
    if get_member_role(member_id) != 'coach':
        return "Only coaches can select teams", 403
    
    coach_teams = get_teams_managed_by_coach(member_id)
    if not any(t['id'] == team_id for t in coach_teams):
        return "Access denied to this team", 403
    
    # Set the selected team in session
    set_primary_team_id_for_context(team_id)
    
    # Find the team name for the success message
    selected_team = next((t for t in coach_teams if t['id'] == team_id), None)
    team_name = selected_team['name'] if selected_team else team_id
    
    response = make_response('')
    response.headers['HX-Trigger'] = json.dumps({
        "showMessage": {"value": f"Switched to team: {team_name}", "target": "body"}
    })
    response.headers['HX-Refresh'] = 'true'  # Refresh the page to update menu and context
    return response

@bp.route("/members")
@auth.login_required
def members_page(context=None):
    """Show team members based on user's role and team context"""
    from common.fitness.roles_service import get_accessible_members_for_context, get_current_team_context
    
    member_id = get_member_id_from_user_context(context)
    accessible_members = get_accessible_members_for_context(member_id)
    current_team = get_current_team_context(member_id)
    
    return hx_render_template('members_page.html', 
                              members=accessible_members,
                              current_team=current_team,
                              context=context)

