import json
from flask import Blueprint, abort, make_response, render_template, request
from hx_common import hx_render_template
from common.fitness.events import EventEntity, create_new_event, list_events, get_event, create_event, store_event, update_event, delete_event, generate_id
bp = Blueprint('schedule', __name__, template_folder='templates')
from auth import auth
from datetime import datetime, timedelta

@bp.route('/')
@auth.login_required
def root(context = None):
    member_id = None
    user = context.get('user', None)
    if user:
        member_id = user.get('sub', None)
    # get today's date
    today = datetime.now().strftime("%Y-%m-%d")
    # add 2 weeks to today's date
    two_weeks_later = (datetime.now() + timedelta(weeks=2)).strftime("%Y-%m-%d")

    events = list_events(member_id, today, two_weeks_later)
    events = sorted(events, key=lambda x: x["datetime_dt"])
    return hx_render_template('event_list.html', context=context, events=events)

@bp.route('/edit_event/<event_id>', methods=['GET', 'POST'])
@auth.login_required
def edit_event(context, event_id):
    user = context.get('user', None)
    if user:
        member_id = user.get('sub', None)
    event = get_event(event_id)
    if not event:
        return abort(404)

    if request.method == 'POST':
        # retrieve the form data
        name = request.form.get('name')
        type = request.form.get('type')
        date = request.form.get('date')
        time = request.form.get('time')

        if name and date and time:
            # ["event_id", "type", "datetime", "name", "description", "location", "owner_member_id", "joined"]
            # event['type'] = type
            event['name'] = name
            event['description'] = request.form.get('description')
            event['location'] = "Cranford YMCA"
            event['datetime'] = f"{date}T{time}"
            event['owner_member_id'] = member_id

            # update the event in the back-end store
            store_event(event)            

            response = make_response('', 204)
            response.headers['HX-Trigger'] = json.dumps({
                # "movieListChanged": None,
                "eventListChanged": None,
                "showMessage": f"{event['name']} updated."
            })
            return response

    return render_template('event_editor.html', event=event, update_url=f"/schedule/edit_event/{event_id}")

@bp.route('/join_event/<event_id>', methods=['GET', 'POST'])
@auth.login_required
def join_event(context, event_id):
    user = context.get('user', None)
    if user:
        member_id = user.get('sub', None)
    event = get_event(event_id)
    if not event:
        return abort(404)

    if request.method == 'POST':
        # retrieve the form data
        activity = request.form.get('activity')

        joined = event.get('joined', [])
        new_joined = []
        for j in joined:
            if j["member_id"] != member_id:
                new_joined.append(j)
        new_joined.append({"member_id": member_id, "activity": activity})

        event['joined'] = new_joined
        store_event(event)            

        response = make_response('', 204)
        response.headers['HX-Trigger'] = json.dumps({
            "eventListChanged": None,
            "showMessage": f"{event['name']} updated."
        })
        return response

    return render_template('join_event.html', event=event, update_url=f"/schedule/join_event/{event_id}")

@bp.route('/create_event', methods=['GET','POST'])
@auth.login_required
def create_event(context=None):
    user = context.get('user', None)
    member_id = user.get('sub', None) if user else None   

    if request.method == 'POST':
        # retrieve the form data
        name = request.form.get('name')
        # type = request.form.get('type')
        date = request.form.get('date')
        time = request.form.get('time')
        description = request.form.get('description')

        if name and date and time:
            event={}
            event['name'] = name
            event['description'] = description
            event['datetime'] = f"{date}T{time}"
            event['location'] = "Cranford YMCA"
            event['owner_member_id'] = member_id
            event['joined'] = []

            # update the event in the back-end store
            store_event(event)            

            response = make_response('', 204)
            response.headers['HX-Trigger'] = json.dumps({
                # "movieListChanged": None,
                "eventListChanged": None,
                "showMessage": f"{event['name']} updated."
            })
            return response

    event = create_new_event(member_id)
    return hx_render_template('event_editor.html', event=None, update_url="/schedule/create_event")


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
def new_event(context=None):
    return hx_render_template('new_event.html', 
                              context=context, 
                              update_url="/event/edit/update")

@bp.route('/event/delete/<event_id>', methods=['POST'])
@auth.login_required
def remove_event(context=None, event_id=None):
    user = context.get('user', None)
    member_id = user.get('sub', None) if user else None   

    event = get_event(event_id)
    if not event:
        return abort(404)
    delete_event(event_id)
    response = make_response('', 204)
    response.headers['HX-Trigger'] = json.dumps({
        "eventListChanged": None,
        "showMessage": f"Event: {event['name']} deleted."
    })
    return response

@bp.route('/leave_event/<event_id>', methods=['POST'])
@auth.login_required
def leave_event(context=None, event_id=None):
    user = context.get('user', None)
    member_id = user.get('sub', None) if user else None   

    event = get_event(event_id)
    if not event:
        return abort(404)
    joined = event.get('joined', [])
    new_joined = []
    for j in joined:
        if j["member_id"] != member_id:
            new_joined.append(j)
    event['joined'] = new_joined
    store_event(event)            
    response = make_response('', 204)
    response.headers['HX-Trigger'] = json.dumps({
        "eventListChanged": None,
        "showMessage": f"Event: {event['name']} updated."
    })
    return response

@bp.route('/event/create', methods=['POST'])
@auth.login_required
def create(context=None):
    print(f"Request: {request.form}")

    event = create_event(request.form)

    return hx_render_template('event_editor.html', 
                              context=context, 
                              event=event,
                              update_url="/event/update")

@bp.route('/edit/update', methods=['POST'])
@auth.login_required
def update_profile(context=None):
    print(f"Request: {request.form}")

    profile = update_event(request.form)
    
    return hx_render_template('profile.html', 
                              context=context, 
                              profile=profile,
                              update_url="/profile/update")


@bp.route('/view_activity', methods=['GET'])
@auth.login_required
def view(context=None, event_id=None):
    event = get_event(event_id)

    return hx_render_template('event_activity_modal.html', 
                              context=context, 
                              update_url="/event/edit/update")    