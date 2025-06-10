import json
from flask import Blueprint, abort, make_response, render_template, request
from common.fitness.member_entity import get_member_detail_from_user_context, get_user_profile
from common.fitness.hx_common import hx_render_template
from common.fitness.workout_sessions import WorkoutSessionEntity, EventTypes, create_new_workout_session, list_workout_sessions, get_workout_session, store_workout_session, delete_workout_session, generate_id
from common.fitness.get_calendar_service import get_calendar_service
bp = Blueprint('schedule', __name__, template_folder='templates')
from auth import auth
from datetime import datetime, timedelta


@bp.route('/')
@auth.login_required
def index(context = None):
    return hx_render_template('schedule.html', context=context)

@bp.route('/calendar')
@auth.login_required
def google_calendar(context = None):
    return render_template('google_calendar.html', context=context)

@bp.route('/your-schedule')
@auth.login_required
def your_schedule(context = None):
    cal = get_calendar_service()
    member = get_member_detail_from_user_context(context)
    member_id = member.get('id', None)
    member_short_name = get_user_profile(member_id).get('short_name', None)

    # here we figure out the date range for the calendar
    # the start date is today, and the end date is 14 days from today
    today = datetime.now()
    start_date = today.strftime("%Y-%m-%d")
    end_date = (today + timedelta(days=14)).strftime("%Y-%m-%d")
    events, _ = cal.get_dates_and_events_stream(date_min=start_date, date_max=end_date)
    return render_template('your_schedule.html', context=context, member_short_name=member_short_name, events=events, member_id=member_id)

@bp.route('/create_event', methods=['GET','POST'])
@auth.login_required
def create_new_event(context=None):
    calendar_service = get_calendar_service()
    member = get_member_detail_from_user_context(context)
    member_id = member.get('id', None)
    profile = get_user_profile(member_id)
    if profile:
        member_short_name = profile.get('short_name', member_id)
    else:
        print(f"Unable to get profile for member id {member_id}")
        abort(404)

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
            # event_meta = f"#member_id:{appt_member_id}\n#created_by:{member_id}"
            event_meta = f"#id={member_id}"            
            calendar_service.add_workout_event(member_short_name=member_short_name, 
                                               event_date=date, event_time=time,
                                               location="YMCA", metadata=event_meta)
            response = make_response('', 204)
            response.headers['HX-Trigger'] = json.dumps({
                "eventListChanged": { "target": "body" },
                 "showMessage": { 
                    "target": "body",
                    "value": f"workout event updated." }
                })
            return response

    return hx_render_template('event_editor.html', event=event, update_url="/schedule/create_event")


@bp.route('/edit_event', methods=['GET', 'POST'])
@auth.login_required
def edit_event(context):

    member = get_member_detail_from_user_context(context)
    member_id = member.get('id', None)
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
        event_id = request.form.get('id')
        date = request.form.get('date')
        time = request.form.get('time')
        event_meta = f"#{member_id}"
        if date and time:
            # update the event in the back-end store
            calendar_service = get_calendar_service()    
            # calendar_service.update_workout_event(id, date, time, member_id)
            event_meta = f"#id={member_id}"            
            calendar_service.update_workout_event(event_id, member_short_name=member_short_name, 
                                                  event_date=date, event_time=time,
                                                  location="YMCA", metadata=event_meta)
            response = make_response('', 204)
            response.headers['HX-Trigger'] = json.dumps({
                "eventListChanged": { "target": "body" },
                "showMessage": {
                    "target": "body",
                    "value": 'f"event updated.'
                }
            })
            return response

    return render_template('event_editor.html', event=event, update_url=f"/schedule/edit_event")

@bp.route('/event_status/<event_id>/<status>', methods=['POST'])
@auth.login_required
def set_event_status(context, event_id, status):

    member = get_member_detail_from_user_context(context)
    member_id = member.get('id', None)
    member_short_name = get_user_profile(member_id).get('short_name', None)

    calendar_service = get_calendar_service()
    event = calendar_service.get_event(event_id)
    datetime = event.get('start', {}).get('dateTime', None)
    tz = event.get('start', {}).get('timeZone', None)
    # datetime has this form:  2025-06-07T06:00:00-04:00'
    # tz is the timezone, e.g. 'America/New_York'
    # we want to convert this to a date and time string
    if datetime:
        # convert the datetime to a date string
        date = datetime.split('T')[0]
        time = datetime.split('T')[1].split('-')[0]
    else:
        date = event.get('start', {}).get('date', None)
        time = event.get('start', {}).get('dateTime', None)

    event_meta = event.get('description', None)
    # event_meta is a string that contains metadata about the event
    # it can be empty, or it main contain details of the member id, such as this:  f"#id={member_id}"
    # or it may contain status information, such as this:  f"#status=cancelled"
    # or it may contain both
    # what this will do is update the status of the event, without removing the existing metadata, just update the status
    if not event_meta:
        event_meta = f"#status={status}"
    else:
        # if the event_meta already contains a status, we will replace it with the new status
        if "#status=" in event_meta:
            event_meta = event_meta.split("#status=")[0] + f"#status={status}"
        else:
            # if it does not contain a status, we will just append the new status
            # check if the event_meta ends with a newline, if it does, we will append the status
            if event_meta.endswith('\n') or event_meta.endswith('\r'):
                event_meta = event_meta + f"#status={status}"
            else:
                event_meta = event_meta + f"\n#status={status}"

    calendar_service.update_workout_event(event_id, member_short_name=member_short_name, 
                                            event_date=date, event_time=time,
                                            location="YMCA", metadata=event_meta)
    response = make_response('', 204)
    response.headers['HX-Trigger'] = json.dumps({
        "eventListChanged": { "target": "body" },
        "showMessage": { "value" : f"event updated.", "target": "body" }
    })
    return response


@bp.route('/delete_event/<id>', methods=['POST'])
@auth.login_required
def remove_workout_session(context=None, id=None):
    member = get_member_detail_from_user_context(context)

    calendar_service = get_calendar_service()    
    calendar_service.delete_workout_event(id)

    response = make_response('', 204)
    response.headers['HX-Trigger'] = json.dumps({
        "eventListChanged": { "target": "body" },
        "showMessage": { "value" : f"Event deleted.", "target": "body" }
    })
    return response
