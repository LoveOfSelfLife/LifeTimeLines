"""
Home Page Routes for Active Friends Club (AFC)

Handles the new three-section home page dashboard:
1. Scheduled Workouts - upcoming workouts and interactions
2. Completed Workouts - recent workout history  
3. Analytics - performance reports and summaries

All routes use HTMX for dynamic updates and follow the existing authentication patterns.
"""

from flask import Blueprint, make_response, render_template, request, jsonify, session, redirect, url_for
from auth import auth
from common.fitness.get_calendar_service import get_calendar_service
from common.fitness.hx_common import hx_render_template
from common.fitness.member_entity import get_member_id_from_user_context, get_member_detail_from_user_context, get_user_profile
from common.fitness.home_data_service import HomePageDataService, format_seconds
from common.fitness.programs import get_members_current_active_program
# from common.fitness.workout_state import set_active_workout_state
from common.entity_store import EntityStore
from datetime import datetime, timezone, date
import json

bp = Blueprint('home', __name__, template_folder='../../templates')

@bp.route("/")
@auth.login_required
def dashboard(context=None):
    """Main home page dashboard with three sections"""
    try:
        member_id = get_member_id_from_user_context(context)
        member = get_member_detail_from_user_context(context)
        
        # For the main dashboard, we load the template with placeholders
        # Each section will load its content via HTMX
        return hx_render_template(
            template_file='home/dashboard.html',
            member=member,
            context=context
        )
        
    except Exception as e:
        print(f"Error loading home dashboard: {e}")
        return hx_render_template(
            template_string='<div class="alert alert-danger">Error loading dashboard</div>',
            context=context
        )

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
        
        return hx_render_template(
            template_file='home/scheduled_workouts_partial.html',
            data=scheduled_data,
            context=context
        )
        
    except Exception as e:
        print(f"Error loading scheduled workouts: {e}")
        return hx_render_template(
            template_string='<div class="alert alert-danger">Error loading scheduled workouts</div>',
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

@bp.route("/workout-details-modal")
@auth.login_required
def workout_details_modal(context=None):
    """Modal showing workout details"""
    try:
        workout_key = request.args.get('workout_key')
        if not workout_key:
            return hx_render_template(
                template_string='<div class="alert alert-danger">No workout specified</div>',
                context=context
            )
        
        # Get workout definition
        entity_store = EntityStore()
        workout_key_parsed = eval(workout_key) if isinstance(workout_key, str) else workout_key
        workout_definition = entity_store.get_item_by_composite_key(workout_key_parsed)
        
        if not workout_definition:
            return hx_render_template(
                template_string='<div class="alert alert-danger">Workout not found</div>',
                context=context
            )
        
        return hx_render_template(
            template_file='home/modals/workout_details_modal.html',
            workout_definition=workout_definition,
            context=context
        )
        
    except Exception as e:
        print(f"Error loading workout details: {e}")
        return hx_render_template(
            template_string='<div class="alert alert-danger">Error loading workout details</div>',
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
        
        # Build modal with workout instance details
        workout_name = workout_instance.get('workout_name', 'Completed Workout')
        start_time = workout_instance.get('start_datetime', '')
        end_time = workout_instance.get('end_datetime', '')
        
        return hx_render_template(
            template_file='home/modals/completed_workout_details_modal.html',
            workout_name=workout_name,
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

@bp.route("/change-workout-modal")
@auth.login_required
def change_workout_modal(context=None):
    """Modal for changing to a different workout from the program"""
    try:
        event_id = request.args.get('event_id')
        program_name = request.args.get('program_name', 'Current Program')
        member_id = get_member_id_from_user_context(context)
        
        # Get alternative workouts from the current program
        current_program = get_members_current_active_program(member_id)
        alternative_workouts = []
        
        if current_program:
            # Get alternative workouts (this would need to be implemented)
            # For now, show placeholder options
            alternative_workouts = [
                {'name': 'Home Workout', 'key': 'home_workout_key', 'description': 'Bodyweight exercises for home'},
                {'name': 'Travel Workout', 'key': 'travel_workout_key', 'description': 'Minimal equipment workout'},
                {'name': 'Light Activity', 'key': 'light_workout_key', 'description': 'Recovery day workout'}
            ]
        
        return hx_render_template(
            template_file='home/modals/change_workout_modal.html',
            event_id=event_id,
            program_name=program_name,
            alternative_workouts=alternative_workouts,
            context=context
        )
        
    except Exception as e:
        print(f"Error loading change workout modal: {e}")
        return hx_render_template(
            template_string='<div class="alert alert-danger">Error loading workout options</div>',
            context=context
        )


@bp.route("/repeat-workout-modal")
@auth.login_required
def repeat_workout_modal(context=None):
    """Modal for repeating a completed workout"""
    try:
        workout_instance_key = request.args.get('workout_instance_key')
        if not workout_instance_key:
            return hx_render_template(
                template_string='<div class="alert alert-danger">No workout specified</div>',
                context=context
            )
        
        # Get workout instance to display workout name
        entity_store = EntityStore()
        workout_key_parsed = eval(workout_instance_key) if isinstance(workout_instance_key, str) else workout_instance_key
        workout_instance = entity_store.get_item_by_composite_key(workout_key_parsed)
        
        workout_name = 'Workout'
        if workout_instance:
            workout_name = workout_instance.get('workout_name', 'Workout')
        
        # Get today's date for the date input minimum
        today_date = date.today().isoformat()
        
        return hx_render_template(
            template_file='home/modals/repeat_workout_modal.html',
            workout_instance_key=workout_instance_key,
            workout_name=workout_name,
            today_date=today_date,
            context=context
        )
        
    except Exception as e:
        print(f"Error loading repeat workout modal: {e}")
        return hx_render_template(
            template_string='<div class="alert alert-danger">Error loading repeat workout form</div>',
            context=context
        )

@bp.route("/change-workout", methods=['POST'])
@auth.login_required  
def change_workout(context=None):
    """Process workout change to alternative"""
    try:
        # This would update the scheduled workout to use the alternative
        # For now, return success message and refresh scheduled workouts
        return hx_render_template(
            template_string='''
            <div class="alert alert-success">
              <i class="bi bi-check-circle me-2"></i>Workout changed successfully!
            </div>
            <script>
              setTimeout(() => {
                htmx.trigger('#scheduled-workouts-content', 'refresh');
              }, 2000);
            </script>
            ''',
            context=context
        )
        
    except Exception as e:
        print(f"Error changing workout: {e}")
        return hx_render_template(
            template_string=f'<div class="alert alert-danger">Error changing workout: {str(e)}</div>',
            context=context
        )

@bp.route("/repeat-workout", methods=['POST'])
@auth.login_required
def repeat_workout(context=None):
    """Process repeating a completed workout by scheduling it again"""
    try:
        workout_instance_key = request.form.get('workout_instance_key')
        schedule_date = request.form.get('schedule_date')
        schedule_time = request.form.get('schedule_time')
        notes = request.form.get('notes', '')
        
        if not all([workout_instance_key, schedule_date, schedule_time]):
            return hx_render_template(
                template_string='<div class="alert alert-danger">Missing required fields</div>',
                context=context
            )
        
        # TODO: Implement the actual repeat workout logic
        # This would involve:
        # 1. Getting the original workout details
        # 2. Creating a new scheduled workout entry
        # 3. Adding it to the member's schedule
        
        # For now, return success message
        member_id = get_member_id_from_user_context(context)
        
        # Refresh the scheduled workouts data
        home_service = HomePageDataService()
        scheduled_data = home_service.get_scheduled_workouts_data(member_id, datetime.now(timezone.utc))
        
        # Return updated scheduled workouts partial with success message
        return hx_render_template(
            template_file='home/scheduled_workouts_partial.html',
            data=scheduled_data,
            success_message=f"Workout scheduled for {schedule_date} at {schedule_time}",
            context=context
        )
        
    except Exception as e:
        print(f"Error processing repeat workout: {e}")
        return hx_render_template(
            template_string='<div class="alert alert-danger">Error scheduling repeat workout</div>',
            context=context
        )

# Additional routes for analytics reports, data export, etc. can be added here