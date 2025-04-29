import json
from flask import Blueprint, abort, make_response, render_template, request
from common.fitness.member_info import get_user_profile
from hx_common import hx_render_template
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



@bp.route('/join_event/<id>', methods=['GET', 'POST'])
@auth.login_required
def join_workout_session(context, id):
    user = context.get('user', None)
    if user:
        member_id = user.get('sub', None)
    workout_session = get_workout_session(id)
    if not workout_session:
        return abort(404)

    if request.method == 'POST':
        # retrieve the form data
        activity = request.form.get('activity')

        joined = workout_session.get('joined', [])
        new_joined = []
        for j in joined:
            if j["member_id"] != member_id:
                new_joined.append(j)
        new_joined.append({"member_id": member_id, "activity": activity})

        workout_session['joined'] = new_joined
        store_workout_session(EventTypes.EVENT_MEMBER_JOINED, workout_session)            

        response = make_response('', 204)
        response.headers['HX-Trigger'] = json.dumps({
            "eventListChanged": None,
            "showMessage": f"{workout_session['name']} updated."
        })
        return response

    return render_template('join_event.html', event=workout_session, update_url=f"/schedule/join_event/{id}")

# TODO: need route for get & post of edit_event
# TODO: need route for create_new_event
# TODO: need route for join event
# TODO: need route for delete_event

# @bp.route('/edit')
# @auth.login_required
# def profile(context=None, event=None):
#     return hx_render_template('event_editor.html', context=context, event=event, update_url="/event/update")

@bp.route('/event/new', methods=['GET'])
@auth.login_required
def new_workout_session(context=None):
    return hx_render_template('new_event.html', 
                              context=context, 
                              update_url="/event/edit/update")


@bp.route('/leave_event/<id>', methods=['POST'])
@auth.login_required
def leave_workout_session(context=None, id=None):
    user = context.get('user', None)
    member_id = user.get('sub', None) if user else None   

    workout_session = get_workout_session(id)
    if not workout_session:
        return abort(404)
    joined = workout_session.get('joined', [])
    new_joined = []
    for j in joined:
        if j["member_id"] != member_id:
            new_joined.append(j)
    workout_session['joined'] = new_joined
    store_workout_session(EventTypes.EVENT_MEMBER_LEFT, workout_session)            
    response = make_response('', 204)
    response.headers['HX-Trigger'] = json.dumps({
        "eventListChanged": None,
        "showMessage": f"Event: {workout_session['name']} updated."
    })
    return response

@bp.route('/event/create', methods=['POST'])
@auth.login_required
def create(context=None):
    print(f"Request: {request.form}")

    workout_session = store_workout_session(request.form)

    return hx_render_template('event_editor.html', 
                              context=context, 
                              event=workout_session,
                              update_url="/event/update")


@bp.route('/view_activity', methods=['GET'])
@auth.login_required
def view(context=None, id=None):
    workout_session = get_workout_session(id)

    return hx_render_template('event_activity_modal.html', 
                              context=context, 
                              update_url="/event/edit/update")    