import json
from flask import Blueprint, abort, make_response, render_template, request
from hx_common import hx_render_template
from common.fitness.workout_sessions import WorkoutSessionEntity, EventTypes, create_new_workout_session, list_workout_sessions, get_workout_session, store_workout_session, delete_workout_session, generate_id
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

    workout_sessions = list_workout_sessions(member_id, today, two_weeks_later)
    workout_sessions = sorted(workout_sessions, key=lambda x: datetime.fromisoformat(x["datetime"]))
    return hx_render_template('event_list.html', context=context, events=workout_sessions)

@bp.route('/edit_event/<id>', methods=['GET', 'POST'])
@auth.login_required
def edit_workout_session(context, id):
    user = context.get('user', None)
    if user:
        member_id = user.get('sub', None)
    workout_session = get_workout_session(id)
    if not workout_session:
        return abort(404)

    if request.method == 'POST':
        # retrieve the form data
        name = request.form.get('name')
        type = request.form.get('type')
        date = request.form.get('date')
        time = request.form.get('time')

        if name and date and time:
            workout_session['name'] = name
            workout_session['description'] = request.form.get('description')
            workout_session['location'] = "Cranford YMCA"
            workout_session['datetime'] = f"{date}T{time}"
            workout_session['owner_member_id'] = member_id

            # update the event in the back-end store
            store_workout_session(EventTypes.EVENT_UPDATED, workout_session)            

            response = make_response('', 204)
            response.headers['HX-Trigger'] = json.dumps({
                # "movieListChanged": None,
                "eventListChanged": None,
                "showMessage": f"{workout_session['name']} updated."
            })
            return response

    return render_template('event_editor.html', event=workout_session, update_url=f"/schedule/edit_event/{id}")

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

@bp.route('/create_event', methods=['GET','POST'])
@auth.login_required
def create_workout_session_handler(context=None):
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
            workout_session={}
            workout_session['name'] = name
            workout_session['description'] = description
            workout_session['datetime'] = f"{date}T{time}"
            workout_session['location'] = "Cranford YMCA"
            workout_session['owner_member_id'] = member_id
            workout_session['joined'] = []

            # update the event in the back-end store
            store_workout_session(EventTypes.EVENT_CREATED, workout_session)            

            response = make_response('', 204)
            response.headers['HX-Trigger'] = json.dumps({
                # "movieListChanged": None,
                "eventListChanged": None,
                "showMessage": f"{workout_session['name']} updated."
            })
            return response

    workout_session = create_new_workout_session(member_id)
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
def new_workout_session(context=None):
    return hx_render_template('new_event.html', 
                              context=context, 
                              update_url="/event/edit/update")

@bp.route('/event/delete/<id>', methods=['POST'])
@auth.login_required
def remove_workout_session(context=None, id=None):
    user = context.get('user', None)
    member_id = user.get('sub', None) if user else None   

    workout_session = get_workout_session(id)
    if not workout_session:
        return abort(404)
    delete_workout_session(id)
    response = make_response('', 204)
    response.headers['HX-Trigger'] = json.dumps({
        "eventListChanged": None,
        "showMessage": f"Event: {workout_session['name']} deleted."
    })
    return response

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