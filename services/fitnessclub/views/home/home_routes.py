"""
Home Page Routes for Active Friends Club (AFC)

Handles the new three-section home page dashboard:
1. Scheduled Workouts - upcoming workouts and interactions
2. Completed Workouts - recent workout history  
3. Analytics - performance reports and summaries

All routes use HTMX for dynamic updates and follow the existing authentication patterns.
"""

from flask import Blueprint, abort, make_response, render_template, render_template_string, request, jsonify, session, redirect, url_for
from auth import auth
from common.fitness.get_calendar_service import get_calendar_service
from common.fitness.hx_common import hx_render_template
from common.fitness.member_entity import get_member_id_from_user_context, get_member_detail_from_user_context, get_user_profile
from common.fitness.home_data_service import HomePageDataService, format_seconds
from common.fitness.member_workout_entity import WorkoutDefinitionEntity
from common.fitness.programs import get_last_workout_instance_for_workout, get_members_current_active_program, get_program_workouts
# from common.fitness.workout_state import set_active_workout_state
from common.entity_store import EntityStore
from datetime import datetime, timezone, date
import json
from common.fitness.analytics.query import AFCAnalyticsRepository

bp = Blueprint('home', __name__, template_folder='../../templates')


@bp.route("/scheduled-workouts")
@auth.login_required  
def scheduled_workouts_partial(context=None):
    return scheduled_workouts_partial2(context)

def scheduled_workouts_partial2(context=None):
    """HTMX partial for scheduled workouts section"""
    try:
        member_id = get_member_id_from_user_context(context)
        
        # Get scheduled workouts data
        home_service = HomePageDataService()
        scheduled_data = home_service.get_scheduled_workouts_data(member_id, datetime.now(timezone.utc))
        
        # Get alternative workout options for select elements
        current_program = get_members_current_active_program(member_id)
        current_prog_workouts = []
        
        if current_program:
            # Create alternative workout options
            for workout_def in get_program_workouts(current_program, member_id):
                workout_info = {
                    'key': str(workout_def.get_composite_key()),
                    'name': workout_def.get('name', 'Unnamed Workout'),
                    'description': workout_def.get('description', '')
                    }
                current_prog_workouts.append(workout_info)
        
        return hx_render_template(
            template_file='home/scheduled_workouts_partial.html',
            data=scheduled_data,
            program_workouts=current_prog_workouts,
            context=context
        )
        
    except Exception as e:
        print(f"Error loading scheduled workouts: {e}")
        return hx_render_template(
            template_string='<div class="alert alert-danger">Error loading scheduled workouts</div>',
            context=context
        )

@bp.route("/adhoc-workouts")
@auth.login_required  
def adhoc_workouts_partial(context=None):
    return adhoc_workouts_partial2(context)

def adhoc_workouts_partial2(context=None):
    """HTMX partial for adhoc workouts section"""
    try:
        member_id = get_member_id_from_user_context(context)
        
        current_program = get_members_current_active_program(member_id)
        prog_workouts = []
        
        if current_program:
            # Get all workouts from the program
            all_program_workouts = get_program_workouts(current_program, member_id)
            
            # Create alternative workout options
            for workout_def in all_program_workouts:
                workout_info = {
                    'key': str(workout_def.get_composite_key()),
                    'name': workout_def.get('name', 'Unnamed Workout'),
                    'description': workout_def.get('description', '')
                    }
                prog_workouts.append(workout_info)
        
        return hx_render_template(
            template_file='home/adhoc_workouts_partial.html',
            program_workouts=prog_workouts,
            program_key = str(current_program.get_composite_key()) if current_program else None,
            context=context
        )
        
    except Exception as e:
        print(f"Error loading adhoc workouts: {e}")
        return hx_render_template(
            template_string=f'<div class="alert alert-danger">Error loading adhoc workouts: {str(e)}</div>',
            context=context
        )

@bp.route("/completed-workouts")
@auth.login_required
def completed_workouts_partial(context=None):
    """HTMX partial for completed workouts section"""
    try:
        member_id = get_member_id_from_user_context(context)
        
        # Get completed workouts data
        home_service = HomePageDataService()
        completed_data = home_service.get_completed_workouts_data(member_id, datetime.now(timezone.utc))
        
        return hx_render_template(
            template_file='home/completed_workouts_partial.html',
            data=completed_data,
            context=context
        )
        
    except Exception as e:
        print(f"Error loading completed workouts: {e}")
        return hx_render_template(
            template_string='<div class="alert alert-danger">Error loading completed workouts</div>',
            context=context
        )

@bp.route("/analytics")
@auth.login_required
def analytics_partial(context=None):
    """HTMX partial for analytics section"""
    member_id = get_member_id_from_user_context(context)

    try:

        # ar = AFCAnalyticsRepository(db_path="/share/FitnessClub/Analytics/afc_analytics.sqlite")
        ar = AFCAnalyticsRepository(db_path="D:/GitHub/DickKemp/LifeTimeLines/test/fitness/fitness_reporting/afc_analytics.sqlite")
        summary = ar.member_dashboard_summary(member_id)
        if summary:
            return render_template_string(f'''
            <div class="row">
                <div class="col-md-4">
                    <div class="card mb-3">
                        <div class="card-body">
                            <h5 class="card-title">workouts per week</h5>
                            <p class="card-text display-4">{summary.get('workouts_per_week', 0)}</p>
                        </div>
                    </div>
                </div>
            </div>
        ''')
    except Exception as e:
        try:
            member_id = get_member_id_from_user_context(context)
            
            # Get analytics data
            home_service = HomePageDataService()
            analytics_data = home_service.get_analytics_data(member_id, datetime.now(timezone.utc))
            
            return hx_render_template(
                template_file='home/analytics_partial.html', 
                data=analytics_data,
                context=context
            )
        
        except Exception as e:
            print(f"Error loading analytics: {e}")
            return hx_render_template(
                template_string='<div class="alert alert-danger">Error loading analytics</div>',
                context=context
            )

@bp.route("/start-workout", methods=['POST'])
@auth.login_required
def start_workout(context=None):
    """Redirect to existing start workout functionality"""
    try:
        # Get form data
        event_id = request.form.get('event_id')
        workout_key = request.form.get('workout_key')
        
        if not workout_key:
            return hx_render_template(
                template_string='<div class="alert alert-danger">No workout specified</div>',
                context=context
            )
        
        # Redirect to existing start workout route in program module
        # This will handle all the complex workout starting logic
        from flask import redirect
        return redirect(url_for('program.start_workout', workout_key=workout_key))
        
    except Exception as e:
        print(f"Error starting workout: {e}")
        return hx_render_template(
            template_string=f'<div class="alert alert-danger">Error starting workout: {str(e)}</div>',
            context=context
        )

@bp.route("/completed-workout-details-modal")
@auth.login_required
def completed_workout_details_modal(context=None):
    """Modal showing completed workout details"""
    try:
        workout_instance_key = request.args.get('workout_instance_key')
        if not workout_instance_key:
            return hx_render_template(
                template_string='<div class="alert alert-danger">No workout specified</div>',
                context=context
            )
        
        # Get workout instance
        entity_store = EntityStore()
        workout_key_parsed = eval(workout_instance_key) if isinstance(workout_instance_key, str) else workout_instance_key
        workout_instance = entity_store.get_item_by_composite_key(workout_key_parsed)
        
        if not workout_instance:
            return hx_render_template(
                template_string='<div class="alert alert-danger">Workout not found</div>',
                context=context
            )

        from views.workouts.workout_routes import (
            extract_workout_parameters_for_workout,
            get_exercises_from_workout,
            get_workout_sections,
        )

        def _format_dt(dt_value):
            if not dt_value:
                return None
            if isinstance(dt_value, datetime):
                return dt_value.strftime('%b %d, %Y %I:%M %p')
            try:
                return datetime.fromisoformat(dt_value).strftime('%b %d, %Y %I:%M %p')
            except (TypeError, ValueError):
                return dt_value
        
        # Reuse the workout viewer parameter extraction for a read-only completed workout view.
        workout_sections = get_workout_sections(workout_instance)
        workout_exercises = get_exercises_from_workout(workout_instance)
        exercises = {exercise.get('id'): exercise for exercise in workout_exercises}
        exercise_parameters_map = extract_workout_parameters_for_workout(
            workout_instance_key,
            workout_instance,
            exercises,
            {},
            ''
        )

        populated_sections = []
        for section in workout_sections:
            section_items = []
            for item in section.get('exercises', []):
                exercise = exercises.get(item.get('id'))
                if exercise:
                    section_items.append({
                        'exercise': exercise,
                        'param_list': exercise_parameters_map.get(section.get('name'), {}).get(exercise.get('id'), {}).get('param_list', [])
                    })
            if section_items:
                populated_sections.append({
                    'name': section.get('name'),
                    'items': section_items
                })

        workout_name = workout_instance.get('workout_name') or workout_instance.get('name') or 'Completed Workout'

        start_time = _format_dt(
            workout_instance.get('start_datetime') or workout_instance.get('started_ts')
        )
        end_time = _format_dt(
            workout_instance.get('end_datetime') or workout_instance.get('finished_ts')
        )
        
        return hx_render_template(
            template_file='home/modals/completed_workout_details_modal.html',
            workout_instance=workout_instance,
            workout_name=workout_name,
            workout_sections=populated_sections,
            start_time=start_time,
            end_time=end_time,
            context=context
        )
        
    except Exception as e:
        print(f"Error loading completed workout details: {e}")
        return hx_render_template(
            template_string='<div class="alert alert-danger">Error loading workout details</div>',
            context=context
        )

@bp.route("/reschedule-workout-modal") 
@auth.login_required
def reschedule_workout_modal(context=None):
    member_id = get_member_id_from_user_context(context)
    member_short_name = get_user_profile(member_id).get('short_name', None)


    event_id = request.args.get('event_id')
    event_date = request.args.get('date', None)
    event_date_dt = datetime.strptime(event_date, '%Y-%m-%d %H:%M:%S%z') if event_date else None
    event_time = request.args.get('time', None)    
    event_time_dt = datetime.strptime(event_time, '%Y-%m-%d %H:%M:%S%z') if event_time else None
    program_name = request.args.get('program_name', 'Current Program')
    event = {
            "id": event_id,
            "date": event_date_dt.strftime('%Y-%m-%d') if event_date_dt else None,
            "time": event_time_dt.strftime('%H:%M') if event_time_dt else None,
            "member": member_short_name,
            "member_id": member_id
        }
    return hx_render_template(
        template_file='home/modals/reschedule_workout_modal.html',
        event=event,
        context=context
    )

@bp.route("/reschedule-workout", methods=['POST'])
@auth.login_required
def reschedule_workout(context=None):
    """Process workout rescheduling"""
    try:
        member_id = get_member_id_from_user_context(context)
        member_short_name = get_user_profile(member_id).get('short_name', None)
        # This would integrate with calendar service to reschedule
        # For now, return success message and refresh scheduled workouts
        event_id = request.form.get('event_id')
        new_date = request.form.get('new_date')
        new_time = request.form.get('new_time')
        reason = request.form.get('reason', '')

        # TODO: we want to post a message to the member's activity feed about the reschedule 
        # with the reason, and also log it in the workout history for that workout instance

        if new_date and new_time:
            # update the event in the back-end store
            calendar_service = get_calendar_service()    
            event_meta = f"#id={member_id}"            
            calendar_service.update_workout_event(event_id, member_short_name=member_short_name, 
                                                  event_date=new_date, event_time=new_time,
                                                  location="YMCA", metadata=event_meta)
            content = scheduled_workouts_partial2(context)  # get updated scheduled workouts partial
            response = make_response(content, 200)
            response.headers['HX-Trigger'] = json.dumps({
                "contentChanged": { "target": "body" },
                "showMessage": {
                    "target": "body",
                    "value": "event updated."
                }
            })
            return response

        
    except Exception as e:
        print(f"Error rescheduling workout: {e}")
        return hx_render_template(
            template_string=f'<div class="alert alert-danger">Error rescheduling workout: {str(e)}</div>',
            context=context
        )

@bp.route("/confirm-start-workout", methods=['GET', 'POST'])
@auth.login_required
def confirm_start_workout(context=None):
    """Simple confirmation dialog for starting a workout"""
    try:
        # Handle both GET (from play button) and POST (from form with select)
        if request.method == 'GET':
            workout_key = request.args.get('workout_key')
            workout_name = request.args.get('workout_name', 'Workout')
        else:  # POST
            workout_key = request.form.get('workout_key')
            # Get workout name from key by looking up the workout
            member_id = get_member_id_from_user_context(context)
            current_program = get_members_current_active_program(member_id)
            if current_program:
                program_workouts = get_program_workouts(current_program, member_id)
                workout_name = 'Selected Workout'  # Default
                for workout_def in program_workouts:
                    if str(workout_def.get_composite_key()) == workout_key:
                        workout_name = workout_def.get('name', 'Selected Workout')
                        break
            else:
                workout_name = 'Selected Workout'
        
        program_key = request.args.get('program_key', '') or request.form.get('program_key', '')
        event_id = request.args.get('event_id', '') or request.form.get('event_id', '')
        
        return hx_render_template(
            template_file='home/modals/confirm_start_workout.html',
            workout_key=workout_key,
            workout_name=workout_name,
            program_key=program_key,
            event_id=event_id,
            context=context
        )
        
    except Exception as e:
        print(f"Error loading start confirmation: {e}")
        return hx_render_template(
            template_string='<div class="alert alert-danger">Error loading confirmation</div>',
            context=context
        )

@bp.route("/update-peek-button", methods=['GET'])
@auth.login_required
def update_peek_button(context=None):
    """Update peek button state based on workout selection"""
    workout_key = request.args.get('workout_key', '')
    button_id = request.args.get('button_id', 'peek-workout-btn')  # default button ID if not provided
    # Determine button state based on selection
    use_last_instance = False
    if workout_key and workout_key.strip():
        (wkt_id, mbr_id, entity) = eval(workout_key) if isinstance(workout_key, str) else workout_key
        member_id = get_member_id_from_user_context(context)
        if not member_id:
            abort(401)
        last_instance = get_last_workout_instance_for_workout(wkt_id, member_id)
        if last_instance and last_instance.get('next_time_workout_sections', None):
            workout_key = last_instance.get_composite_key()
            use_last_instance = True
        
        # Properly escape the workout_key for JSON and HTML
        hx_vals_json = json.dumps({
            "key": str(workout_key),
            "is_modal": "true",
            "use_last_instance": str(use_last_instance).lower()
        })
        # Escape quotes for HTML attribute
        hx_vals_escaped = hx_vals_json.replace('"', '&quot;')
        
        button_html = f'''
        <button id="{button_id}"
                type="button"
                class="btn btn-light btn-sm rounded-0 rounded-end"
                title="Preview selected workout"
                hx-get="/workouts/viewer/workout"
                hx-vals="{hx_vals_escaped}"
                hx-target="#modals-here"
                hx-swap="innerHTML"
                style="border-left: 1px solid rgba(0,0,0,0.125);">
          <i class="bi bi-eye me-1"></i>
        </button>
        '''
    else:
        button_html = f'''
        <button id="{button_id}"
                type="button"
                class="btn btn-light btn-sm rounded-0 rounded-end"
                disabled
                title="Select a workout to peek"
                style="border-left: 1px solid rgba(0,0,0,0.125);">
          <i class="bi bi-eye me-1"></i>
        </button>
        '''
    
    return hx_render_template(
        template_string=button_html,
        context=context
    )
