import json
from flask import Blueprint, abort, make_response, render_template, request
from common.fitness.coach_team_entity import get_team_coaches
from common.fitness.member_entity import get_member_id_from_user_context, get_user_profile
from common.fitness.hx_common import hx_render_template
from common.fitness.member_team_entity import get_team_members
from common.fitness.roles_service import get_accessible_members_for_context, get_current_team_context, get_member_role_context
from common.fitness.workout_sessions import WorkoutSessionEntity, EventTypes, create_new_workout_session, list_workout_sessions, get_workout_session, store_workout_session, delete_workout_session, generate_id
from common.fitness.get_calendar_service import get_calendar_service
bp = Blueprint('schedule', __name__, template_folder='templates')
from auth import auth
from datetime import datetime, timedelta

WEEKDAY_LABELS = [
    ("MO", "Monday"),
    ("TU", "Tuesday"),
    ("WE", "Wednesday"),
    ("TH", "Thursday"),
    ("FR", "Friday"),
    ("SA", "Saturday"),
    ("SU", "Sunday"),
]

WEEKDAY_TO_INDEX = {
    "MO": 0,
    "TU": 1,
    "WE": 2,
    "TH": 3,
    "FR": 4,
    "SA": 5,
    "SU": 6,
}


def _get_first_occurrence_date(start_date, event_time, byday_values):
    """Return the first date/time in the recurrence after now and not before start_date."""
    now_dt = datetime.now()
    selected_weekdays = {WEEKDAY_TO_INDEX[day] for day in byday_values if day in WEEKDAY_TO_INDEX}
    if not selected_weekdays:
        return None

    for offset in range(0, 370):
        candidate_date = start_date + timedelta(days=offset)
        if candidate_date.weekday() not in selected_weekdays:
            continue
        candidate_dt = datetime.combine(candidate_date, event_time)
        if candidate_dt > now_dt:
            return candidate_date

    return None


def _normalize_weekdays(selected_days):
    ordered_unique_days = []
    for day_code, _ in WEEKDAY_LABELS:
        if day_code in selected_days:
            ordered_unique_days.append(day_code)
    return ordered_unique_days


def _build_hx_trigger_response(message):
    response = make_response('', 204)
    response.headers['HX-Trigger'] = json.dumps({
        "eventListChanged": {"target": "body"},
        "showMessage": {
            "target": "body",
            "value": message
        }
    })
    return response


@bp.route('/')
@auth.login_required
def index(context = None):
    return hx_render_template('schedule.html', context=context)

@bp.route('/calendar')
@auth.login_required
def google_calendar(context = None):
    return render_template('google_calendar.html', context=context)

@bp.route('/schedule-by-time-slots')
@auth.login_required
def schedule_by_time_slots(context = None):
    cal = get_calendar_service()
    member_id = get_member_id_from_user_context(context)
    member_short_name = get_user_profile(member_id).get('short_name', None)

    # here we figure out the date range for the calendar
    # the start date is today, and the end date is 14 days from today
    today = datetime.now()
    start_date = today.strftime("%Y-%m-%d")
    end_date = (today + timedelta(days=14)).strftime("%Y-%m-%d")
    current_team = get_current_team_context(member_id)        
    team_members = get_team_members(current_team['id'])
    team_coaches = get_team_coaches(current_team['id'])
    all_members_of_team = [tm.get('member_id') for tm in team_members] + [tc.get('coach_id') for tc in team_coaches]         
    team_member_filter_func = lambda m_id: any(tm_id == m_id for tm_id in all_members_of_team)
    events, _ = cal.get_dates_and_events_stream(date_min=start_date, date_max=end_date, filter_by_member_id_func=team_member_filter_func)
    
    # Get user profiles for all members in the events
    user_profiles = {}
    for event in events:
        if event.get('member_id') and event['member_id'] not in user_profiles:
            profile = get_user_profile(event['member_id'])
            user_profiles[event['member_id']] = profile
            # Debug: print profile info
            print(f"DEBUG: Member ID: {event['member_id']}, Profile: {profile}")
    
    return render_template('schedule_by_time_slots.html', context=context, member_short_name=member_short_name, 
                         events=events, member_id=member_id, user_profiles=user_profiles)

def prepare_schedule(entries):
    sorted_sched = sorted(entries, key=lambda x: x['datetime'])
    return [{**e, 'date': e['datetime'].date()} for e in sorted_sched]

# @bp.template_filter('format_datetime')
def format_datetime(value, fmt="%A, %b %d, %I:%M %p"):
    return value.strftime(fmt)
bp.add_app_template_filter(format_datetime, name='format_datetime')


@bp.route('/create_event', methods=['GET','POST'])
@auth.login_required
def create_new_event(context=None):
    calendar_service = get_calendar_service()
    member_id = get_member_id_from_user_context(context)
    role_context = get_member_role_context(member_id)
    accessible_members = get_accessible_members_for_context(member_id)
    accessible_member_ids = {str(m.get('id')) for m in accessible_members if m and m.get('id')}

    assigned_member_id = request.args.get('assigned_member_id', member_id)
    if role_context.get('role') == 'coach':
        if str(assigned_member_id) not in accessible_member_ids:
            assigned_member_id = member_id
    else:
        assigned_member_id = member_id

    profile = get_user_profile(assigned_member_id)
    if profile:
        member_short_name = profile.get('short_name', assigned_member_id)
    else:
        print(f"Unable to get profile for member id {assigned_member_id}")
        abort(404)

    event = None
    optional_date = request.args.get('date', None)
    optional_time = request.args.get('time', None)

    if optional_date:
        event = {
            "id": "",
            "date": optional_date,
            "time": optional_time if optional_time else "",
            "member_id": member_id,
            "assigned_to_member_id": assigned_member_id
        }
    else:
        event = {
            "id": "",
            "date": "",
            "time": "",
            "member_id": member_id,
            "assigned_to_member_id": assigned_member_id
        }

    if request.method == 'POST':
        # retrieve the form data
        date = request.form.get('date')
        time = request.form.get('time')
        selected_member_id = request.form.get('assigned_member_id', member_id)

        if role_context.get('role') == 'coach':
            if str(selected_member_id) in accessible_member_ids:
                assigned_member_id = selected_member_id
            else:
                assigned_member_id = member_id
        else:
            assigned_member_id = member_id

        profile = get_user_profile(assigned_member_id)
        if profile:
            member_short_name = profile.get('short_name', assigned_member_id)
        else:
            print(f"Unable to get profile for member id {assigned_member_id}")
            abort(404)

        event['assigned_to_member_id'] = assigned_member_id

        if date and time:
            # update the event in the back-end store
            # event_meta = f"#member_id:{appt_member_id}\n#created_by:{member_id}"
            event_meta = f"#id={assigned_member_id}\n#created_by={member_id}"
            calendar_service.add_workout_event(member_short_name=member_short_name, 
                                               event_date=date, event_time=time,
                                               location="YMCA", metadata=event_meta)
            response = make_response('', 204)
            response.headers['HX-Trigger'] = json.dumps({
                "eventListChanged": { "target": "body" },
                 "showMessage": { 
                    "target": "body",
                    "value": "workout event saved" }
                })
            return response

    return hx_render_template(
        'event_editor.html',
        event=event,
        update_url="/schedule/create_event",
        accessible_members=accessible_members,
        role_context=role_context,
        show_assignment=True
    )


@bp.route('/recurring_action_choice')
@auth.login_required
def recurring_action_choice(context=None):
    action = request.args.get('action', 'edit')
    event = {
        'id': request.args.get('id', ''),
        'date': request.args.get('date', ''),
        'time': request.args.get('time', ''),
        'recurring_event_id': request.args.get('recurring_event_id', '')
    }
    if action not in ['edit', 'delete']:
        abort(400)
    if not event['id'] or not event['recurring_event_id']:
        abort(400)

    return hx_render_template(
        'recurring_action_choice.html',
        action=action,
        event=event
    )


@bp.route('/create_recurring_event', methods=['GET', 'POST'])
@auth.login_required
def create_recurring_event(context=None):
    calendar_service = get_calendar_service()
    member_id = get_member_id_from_user_context(context)
    role_context = get_member_role_context(member_id)
    accessible_members = get_accessible_members_for_context(member_id)
    accessible_member_ids = {str(m.get('id')) for m in accessible_members if m and m.get('id')}

    assigned_member_id = request.args.get('assigned_member_id', member_id)
    if role_context.get('role') == 'coach':
        if str(assigned_member_id) not in accessible_member_ids:
            assigned_member_id = member_id
    else:
        assigned_member_id = member_id

    profile = get_user_profile(assigned_member_id)
    if profile:
        member_short_name = profile.get('short_name', assigned_member_id)
    else:
        print(f"Unable to get profile for member id {assigned_member_id}")
        abort(404)

    today_str = datetime.now().strftime("%Y-%m-%d")
    event = {
        "start_date": request.args.get('start_date', today_str),
        "time": request.args.get('time', "06:00"),
        "days": request.args.getlist('days'),
        "member_id": member_id,
        "assigned_to_member_id": assigned_member_id
    }

    if request.method == 'POST':
        start_date = request.form.get('start_date')
        event_time = request.form.get('time')
        selected_days = _normalize_weekdays(request.form.getlist('days'))
        selected_member_id = request.form.get('assigned_member_id', member_id)

        if role_context.get('role') == 'coach':
            if str(selected_member_id) in accessible_member_ids:
                assigned_member_id = selected_member_id
            else:
                assigned_member_id = member_id
        else:
            assigned_member_id = member_id

        profile = get_user_profile(assigned_member_id)
        if profile:
            member_short_name = profile.get('short_name', assigned_member_id)
        else:
            print(f"Unable to get profile for member id {assigned_member_id}")
            abort(404)

        event['start_date'] = start_date
        event['time'] = event_time
        event['days'] = selected_days
        event['assigned_to_member_id'] = assigned_member_id

        if not selected_days:
            return hx_render_template(
                'recurring_event_editor.html',
                event=event,
                day_options=WEEKDAY_LABELS,
                error_message="Pick at least one day of the week.",
                accessible_members=accessible_members,
                role_context=role_context
            )

        if start_date and event_time:
            try:
                parsed_start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
                parsed_event_time = datetime.strptime(event_time, "%H:%M").time()
            except ValueError:
                return hx_render_template(
                    'recurring_event_editor.html',
                    event=event,
                    day_options=WEEKDAY_LABELS,
                    error_message="Invalid date or time value.",
                    accessible_members=accessible_members,
                    role_context=role_context
                )

            first_occurrence_date = _get_first_occurrence_date(parsed_start_date, parsed_event_time, selected_days)
            if not first_occurrence_date:
                return hx_render_template(
                    'recurring_event_editor.html',
                    event=event,
                    day_options=WEEKDAY_LABELS,
                    error_message="Unable to compute the first occurrence for this recurrence.",
                    accessible_members=accessible_members,
                    role_context=role_context
                )

            byday = ",".join(selected_days)
            event_meta = f"#id={assigned_member_id}\n#created_by={member_id}"
            calendar_service.add_recurring_workout_event(
                member_short_name=member_short_name,
                event_date=first_occurrence_date.strftime("%Y-%m-%d"),
                event_time=event_time,
                frequency="WEEKLY",
                byday=byday,
                location="YMCA",
                metadata=event_meta
            )

            response = make_response('', 204)
            response.headers['HX-Trigger'] = json.dumps({
                "eventListChanged": {"target": "body"},
                "showMessage": {
                    "target": "body",
                    "value": "recurring workout scheduled"
                }
            })
            return response

    return hx_render_template(
        'recurring_event_editor.html',
        event=event,
        day_options=WEEKDAY_LABELS,
        accessible_members=accessible_members,
        role_context=role_context
    )


@bp.route('/edit_event', methods=['GET', 'POST'])
@auth.login_required
def edit_event(context):

    member_id = get_member_id_from_user_context(context)
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
            "member_id": member_id,
            "recurring_event_id": request.args.get('recurring_event_id', '')
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
                    "value": "event updated."
                }
            })
            return response

    return hx_render_template(
        'event_editor.html',
        event=event,
        update_url=f"/schedule/edit_event",
        show_assignment=False
    )


@bp.route('/edit_recurring_event', methods=['GET', 'POST'])
@auth.login_required
def edit_recurring_event(context=None):
    calendar_service = get_calendar_service()
    member_id = get_member_id_from_user_context(context)
    role_context = get_member_role_context(member_id)
    accessible_members = get_accessible_members_for_context(member_id)
    accessible_member_ids = {str(m.get('id')) for m in accessible_members if m and m.get('id')}

    if request.method == 'GET':
        recurring_event_id = request.args.get('recurring_event_id', '')
        if not recurring_event_id:
            abort(400)

        event = calendar_service.get_recurring_workout_event_details(recurring_event_id)
        if not event:
            abort(404)

        event['recurring_event_id'] = recurring_event_id
        event['member_id'] = member_id
        assigned_member_id = event.get('assigned_to_member_id') or event.get('member_id') or member_id
        if role_context.get('role') == 'coach' and str(assigned_member_id) in accessible_member_ids:
            event['assigned_to_member_id'] = assigned_member_id
        else:
            event['assigned_to_member_id'] = member_id

        return hx_render_template(
            'recurring_event_editor.html',
            event=event,
            day_options=WEEKDAY_LABELS,
            accessible_members=accessible_members,
            role_context=role_context,
            update_url='/schedule/edit_recurring_event',
            modal_title='Edit recurring workout',
            submit_label='Save recurring changes'
        )

    recurring_event_id = request.form.get('recurring_event_id', '')
    if not recurring_event_id:
        abort(400)

    start_date = request.form.get('start_date')
    event_time = request.form.get('time')
    selected_days = _normalize_weekdays(request.form.getlist('days'))
    selected_member_id = request.form.get('assigned_member_id', member_id)

    if role_context.get('role') == 'coach' and str(selected_member_id) in accessible_member_ids:
        assigned_member_id = selected_member_id
    else:
        assigned_member_id = member_id

    event = {
        'start_date': start_date,
        'time': event_time,
        'days': selected_days,
        'member_id': member_id,
        'assigned_to_member_id': assigned_member_id,
        'recurring_event_id': recurring_event_id
    }

    profile = get_user_profile(assigned_member_id)
    if profile:
        member_short_name = profile.get('short_name', assigned_member_id)
    else:
        print(f"Unable to get profile for member id {assigned_member_id}")
        abort(404)

    if not selected_days:
        return hx_render_template(
            'recurring_event_editor.html',
            event=event,
            day_options=WEEKDAY_LABELS,
            error_message='Pick at least one day of the week.',
            accessible_members=accessible_members,
            role_context=role_context,
            update_url='/schedule/edit_recurring_event',
            modal_title='Edit recurring workout',
            submit_label='Save recurring changes'
        )

    try:
        datetime.strptime(start_date, "%Y-%m-%d").date()
        datetime.strptime(event_time, "%H:%M").time()
    except (TypeError, ValueError):
        return hx_render_template(
            'recurring_event_editor.html',
            event=event,
            day_options=WEEKDAY_LABELS,
            error_message='Invalid date or time value.',
            accessible_members=accessible_members,
            role_context=role_context,
            update_url='/schedule/edit_recurring_event',
            modal_title='Edit recurring workout',
            submit_label='Save recurring changes'
        )

    byday = ",".join(selected_days)
    event_meta = f"#id={assigned_member_id}\n#created_by={member_id}"
    calendar_service.update_recurring_workout_event(
        recurring_event_id=recurring_event_id,
        member_short_name=member_short_name,
        event_date=start_date,
        event_time=event_time,
        frequency='WEEKLY',
        byday=byday,
        location='YMCA',
        metadata=event_meta
    )
    return _build_hx_trigger_response('Recurring workout updated.')

@bp.route('/event_status/<event_id>/<status>', methods=['POST'])
@auth.login_required
def set_event_status(context, event_id, status):

    member_id = get_member_id_from_user_context(context)
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
    calendar_service = get_calendar_service()
    delete_scope = request.args.get('scope', 'single')
    recurring_event_id = request.args.get('recurring_event_id', '')

    if delete_scope == 'series':
        if not recurring_event_id:
            abort(400)
        calendar_service.delete_recurring_workout_event(recurring_event_id)
        return _build_hx_trigger_response('Recurring series deleted.')

    if delete_scope != 'single':
        abort(400)

    calendar_service.delete_workout_event(id)
    return _build_hx_trigger_response('Event deleted.')
