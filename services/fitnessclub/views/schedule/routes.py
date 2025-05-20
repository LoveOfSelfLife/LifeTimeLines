import json
from flask import Blueprint, abort, make_response, render_template, request
from common.fitness.member_entity import get_user_profile
from common.fitness.hx_common import hx_render_template
from common.fitness.workout_sessions import WorkoutSessionEntity, EventTypes, create_new_workout_session, list_workout_sessions, get_workout_session, store_workout_session, delete_workout_session, generate_id
bp = Blueprint('schedule', __name__, template_folder='templates')
from auth import auth
from datetime import datetime, timedelta
from common.fitness.google_calendar_events import GoogleCalendarService
calendar_service = None 

def get_calendar_service():
    global calendar_service
    if calendar_service is None:
        calendar_service = GoogleCalendarService()
    return calendar_service

@bp.route('/')
@auth.login_required
def root(context = None):
    return hx_render_template('schedule.html', context=context)

@bp.route('/calendar')
@auth.login_required
def google_calendar(context = None):
    return render_template('google_calendar.html', context=context)

@bp.route('/your-schedule')
@auth.login_required
def your_schedule(context = None):
    cal = get_calendar_service()
    user = context.get('user', None)
    if user:
        member_id = user.get('sub', None)
        member_short_name = get_user_profile(member_id).get('short_name', None)    
    # here we figure out the date range for the calendar
    # the start date is today, and the end date is 14 days from today
    today = datetime.now()
    start_date = today.strftime("%Y-%m-%d")
    end_date = (today + timedelta(days=14)).strftime("%Y-%m-%d")
    events = cal.get_dates_and_events_stream(date_min=start_date, date_max=end_date)
    return render_template('your_schedule.html', context=context, member_short_name=member_short_name, events=events)

@bp.route('/create_event', methods=['GET','POST'])
@auth.login_required
def create_new_event(context=None):
    calendar_service = get_calendar_service()
    user = context.get('user', None)
    member_id = user.get('sub', None) if user else None   
    event = None
    optional_date = request.args.get('date', None)

    if optional_date:
        event = { "id": "", "date": optional_date, "time": "" }        
    else:
        event = { "id": "", "date": "", "time": "" }

    if request.method == 'POST':
        # retrieve the form data
        date = request.form.get('date')
        time = request.form.get('time')

        if date and time:
            # update the event in the back-end store
            calendar_service.add_workout_event(member_id, date, time)

            response = make_response('', 204)
            response.headers['HX-Trigger'] = json.dumps({
                "eventListChanged": None,
                 "showMessage": f"workout event updated."
            })
            return response

    return hx_render_template('event_editor.html', event=event, update_url="/schedule/create_event")


@bp.route('/edit_event', methods=['GET', 'POST'])
@auth.login_required
def edit_event(context):

    user = context.get('user', None)
    if user:
        member_id = user.get('sub', None)
        member_short_name = get_user_profile(member_id).get('short_name', None)

    if request.method == 'GET':
    
        event_id = request.args.get('id', None)
        event_date = request.args.get('date', None)
        event_time = request.args.get('time', None)

        event = {
            "id": event_id,
            "date": event_date,
            "time": event_time,
            "member": member_short_name,
            "member_id": member_id
        }

    if request.method == 'POST':
        # retrieve the form data
        id = request.form.get('id')
        date = request.form.get('date')
        time = request.form.get('time')

        if date and time:
            # update the event in the back-end store
            calendar_service = get_calendar_service()    
            calendar_service.update_workout_event(id, date, time, member_id)

            response = make_response('', 204)
            response.headers['HX-Trigger'] = json.dumps({
                "eventListChanged": None,
                "showMessage": f"event updated."
            })
            return response

    return render_template('event_editor.html', event=event, update_url=f"/schedule/edit_event")

@bp.route('/delete_event/<id>', methods=['POST'])
@auth.login_required
def remove_workout_session(context=None, id=None):
    user = context.get('user', None)
    member_id = user.get('sub', None) if user else None   

    # if not workout_session:
        # return abort(404)
    calendar_service = get_calendar_service()    
    calendar_service.delete_workout_event(id)

    response = make_response('', 204)
    response.headers['HX-Trigger'] = json.dumps({
        "eventListChanged": None,
        "showMessage": f"Event deleted."
    })
    return response
