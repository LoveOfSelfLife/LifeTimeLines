from flask import Blueprint, render_template, request
from hx_common import hx_render_template
from common.fitness.events import EventEntity, list_events, get_event, create_event, update_event
bp = Blueprint('schedule', __name__, template_folder='templates')
from auth import auth

@bp.route('/')
@auth.login_required
def root(context = None):
    member_id = None
    user = context.get('user', None)
    if user:
        member_id = user.get('sub', None)
    events = list_events(member_id, 2, 3)
    events = sorted(events, key=lambda x: x["datetime_dt"])
    return hx_render_template('event_list.html', context=context, events=events)

@bp.route('/edit')
@auth.login_required
def profile(context=None, event=None):
    return hx_render_template('event_editor.html', context=context, event=event, update_url="/event/update")

@bp.route('/event/new', methods=['GET'])
@auth.login_required
def new_event(context=None):
    return hx_render_template('new_event.html', 
                              context=context, 
                              update_url="/event/edit/update")

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