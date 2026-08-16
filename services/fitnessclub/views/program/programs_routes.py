import copy
from ast import literal_eval
from datetime import datetime
import json

import uuid
from flask import Blueprint, abort, current_app, make_response, redirect, render_template, request, session, url_for
from common.entity_store import EntityObject, EntityStore
from common.fitness import workout_entity
from common.fitness.active_fitness_registry import get_fitnessclub_listing_fields_for_entity
from common.fitness.cacher import delete_from_cache, get_cache_value, set_cache_value
from common.fitness.entities_getter import delete_entity, get_entity, get_entities
from common.fitness.entity_constants import PROGRAM_ENTITY_NAME, WORKOUT_ENTITY_NAME
from common.fitness.get_calendar_service import get_calendar_service
from common.fitness.hx_common import get_filter_terms_from_request, hx_render_template
from common.fitness.hx_common import rm_spaces
from common.fitness.member_entity import MembershipRegistry, get_member_id_from_user_context, get_user_profile, is_member_an_admin
from common.fitness.member_exercise_history import extract_and_load_exercise_events_from_workout_instance
from common.fitness.member_program_entity import MemberProgramsEntity
from common.fitness.member_workout_entity import MemberWorkoutDefinitionEntity, MemberWorkoutInstanceEntity, get_exercises_from_workout
from common.fitness.programs import get_last_workout_instance_for_workout, get_next_workout_in_program, get_workouts_from_program
from common.fitness.workout_state import clear_active_workout_state, get_active_workout_state, initialize_active_workout_state, update_active_workout_state
from common.fitness.edit_workout_object import bring_up_workouts_builder
from common.fitness.roles_service import get_accessible_members_for_context, get_team_coaches_with_details, get_team_for_client, is_member_client, is_member_coach
from common.fitness.coach_team_entity import get_coachs_team_members
from common.fitness.entities_getter import filter_entities_by_member_role
bp = Blueprint('program', __name__, template_folder='templates')
from auth import auth

PROGRAM_MULTI_SELECT_SESSION_KEY = 'program_builder_selected_workout_keys'


def _normalize_form_datetime(value, fallback=None):
    if not value:
        return fallback

    try:
        return datetime.fromisoformat(value).isoformat()
    except ValueError:
        return fallback


def _as_bool(value, default=False):
    if value is None:
        return default
    return str(value).strip().lower() in ('1', 'true', 'yes', 'on')


def _resolve_selected_workout_keys(allow_multi_select=False):
    if not allow_multi_select:
        session.pop(PROGRAM_MULTI_SELECT_SESSION_KEY, None)
        return []

    selected_keys = [str(key) for key in session.get(PROGRAM_MULTI_SELECT_SESSION_KEY, []) if key]
    selected_keys = list(dict.fromkeys(selected_keys))

    toggle_key_raw = request.form.get('multi_select_toggle_key')
    toggle_key = str(toggle_key_raw) if toggle_key_raw else None

    if toggle_key is not None:
        posted_checked_values = set(str(value) for value in request.form.getlist('selected_entity_keys') if value)
        if toggle_key in posted_checked_values:
            if toggle_key not in selected_keys:
                selected_keys.append(toggle_key)
        else:
            selected_keys = [key for key in selected_keys if key != toggle_key]

        session[PROGRAM_MULTI_SELECT_SESSION_KEY] = selected_keys
        return selected_keys

    posted_selected_keys = [str(key) for key in request.form.getlist('selected_entity_keys') if key]
    if posted_selected_keys:
        selected_keys = list(dict.fromkeys(posted_selected_keys))

    session[PROGRAM_MULTI_SELECT_SESSION_KEY] = selected_keys
    return selected_keys

@bp.route('/')
@auth.login_required
def index(context=None):
    member_id = get_member_id_from_user_context(context)
    if not member_id:
        abort(401)
    return programs_listing2(context)

@bp.route('/programs-listing', methods=['GET', 'POST'])
@auth.login_required
def programs_listing(context=None):
    member_id = get_member_id_from_user_context(context)
    if not member_id:
        abort(401)
    return programs_listing2(context)

def programs_listing2(context=None):
    entity_name = PROGRAM_ENTITY_NAME
    page = int(request.args.get('page', 1))
    page_size = 100
    member_id = get_member_id_from_user_context(context)
    if not member_id:
        abort(401)
    # Handle view preference
    view = (request.form.get('view') if request.method == 'POST' 
            else request.args.get('view')) or session.get('view_preference', 'list')
    
    if view != session.get('view_preference'):
        session['view_preference'] = view
    
    fields_to_display = get_fitnessclub_listing_fields_for_entity(entity_name)
    filter_terms = get_filter_terms_from_request()

    member_id = get_member_id_from_user_context(context)
    if not member_id:
        abort(401)
    entities = get_entities(entity_name, fields_to_display, filter_terms, partition_key=member_id, member_id=member_id)
    entities = filter_entities_by_member_role(member_id, entities)

    sort_by='end_date'
    sort_ascending=False
    sort_key = lambda x: str(x.get('entity', {}).get(sort_by, '')).lower()

    entities = sorted(entities, key=sort_key, reverse=not sort_ascending)    
    return program_listing_base(context, entity_name, page, page_size, view, fields_to_display, filter_terms, entities)

def program_listing_base(context, entity_name, page, page_size, view, fields_to_display, filter_terms, entities):
    total_pages = (len(entities) + page_size - 1) // page_size
    start = (page - 1) * page_size
    end = start + page_size
    current = entities[start:end]
    if request.headers.get('HX-Target') == 'results-area':
        template_file_name = 'entity_results_partial.html'
    else:
        template_file_name = 'entity_list_component.html'
    
    # Set results_target_container based on request args
    target = request.args.get('target')
    results_target_container = target if target else 'results-area'
    
    # displays workouts at the top level
    return hx_render_template(
        template_file_name,
        title="Programs Library",
        entity_name=entity_name,
        main_content_container="entities-container",        
        fields_to_display=fields_to_display,
        entities=current,
        filter_terms=filter_terms,
        args=request.args,
        page=page,
        view=view,
        entity_add_route=f"{url_for('program.builder_new')}?x=1",        
        total_pages=total_pages,
        entity_view_route=f'/program/viewer?entity_table={entity_name}',
        entities_listing_route=f'/program/programs-listing?entity_table={entity_name}',
        entity_action_route=f'/program/edit?entity_table={entity_name}',
        entity_action_icon='bi-pencil-square',  
        entity_action_label='Edit Program',
        favorite_toggle_route='/admin/toggle-favorite',
        results_target_container=results_target_container,
        entity_card_view_html='program_card_view.html',
        context=context)

@bp.route('/viewer')
@auth.login_required
def program_viewer(context=None):
    # Get the composite key from query parameters
    composite_key_str = request.args.get('key', None)
    if not composite_key_str:
        abort(400, "Missing program key")
    
    try:
        composite_key = eval(composite_key_str)
    except:
        abort(400, "Invalid program key format")
    
    # Fetch the program entity
    es = EntityStore()
    program_data = es.get_item_by_composite_key(composite_key)
    if not program_data:
        abort(404, "Program not found")
    
    eoclass = EntityObject.get_entity_class_from_table_name(PROGRAM_ENTITY_NAME)
    program = eoclass(program_data)
    
    # Get workouts for this program
    workouts = get_workouts_from_program(program)
    
    # Separate standard and alternative workouts
    standard_workouts = [w for w in workouts if w.get('workout_type', 'standard') == 'standard']
    alternative_workouts = [w for w in workouts if w.get('workout_type', 'standard') == 'alternative']
    
    # Get member information
    assigned_member_id = program.get('assigned_to_member_id') or program.get('member_id')
    member = get_entity('MemberTable', assigned_member_id)
    member_name = member.get('name', 'Unknown Member') if member else 'Unknown Member'
    
    return hx_render_template(
        "program_viewer.html",
        program=program,
        member_name=member_name,
        standard_workouts=standard_workouts,
        alternative_workouts=alternative_workouts,
        context=context
    )    

@bp.route('/workouts-listing', methods=['GET', 'POST'])
@auth.login_required
def workouts_listing(context=None):
    entity_name = WORKOUT_ENTITY_NAME
    program_id = request.args.get('program_id')
    page = int(request.args.get('page', 1))
    target = request.args.get('target')
    page_size = 100
    member_id = get_member_id_from_user_context(context)
    if not member_id:
        abort(401)
    # Handle view preference
    view = (request.form.get('view') if request.method == 'POST' 
            else request.args.get('view')) or session.get('view_preference', 'list')
    
    if view != session.get('view_preference'):
        session['view_preference'] = view
    
    fields_to_display = get_fitnessclub_listing_fields_for_entity(entity_name)
    filter_terms = get_filter_terms_from_request()

            
    # mobile = request.args.get('mobile', type=bool, default=False)
    # div_id = 'lib-list-mobile' if mobile else 'lib-list'
    div_id = target
    current_program = get_cache_value('current_program')

    if current_program:
        if current_program['id'] != program_id:
            abort(404)
    else:
            abort(404)     

    allow_multi_select = _as_bool(request.form.get('allow_multi_select', None),
                                  _as_bool(request.args.get('allow_multi_select', None), False))
    selected_entity_keys = _resolve_selected_workout_keys(allow_multi_select=allow_multi_select)
    # modal_mode = _as_bool(request.args.get('modal_mode', None), False) if request.method == 'GET' else _as_bool(request.form.get('modal_mode', None), False)   
    entities = get_entities(entity_name, fields_to_display, filter_terms, member_id=member_id)
    entities = filter_entities_by_member_role(member_id, entities)

    return workouts_listing_base(
        context,
        entity_name,
        program_id,
        page,
        target,
        view,
        page_size,
        fields_to_display,
        div_id,
        filter_terms,
        entities,
        allow_multi_select=allow_multi_select,
        selected_entity_keys=selected_entity_keys,
        modal_mode=False,
    )


@bp.route('/workouts-listing-modal', methods=['GET'])
@auth.login_required
def workouts_listing_modal(context=None):
    member_id = get_member_id_from_user_context(context)
    if not member_id:
        abort(401)

    program_id = request.args.get('program_id')
    if not program_id:
        abort(400)

    current_program = get_cache_value('current_program')
    if not current_program or current_program.get('id') != program_id:
        abort(404)

    session[PROGRAM_MULTI_SELECT_SESSION_KEY] = []

    page = int(request.args.get('page', 1))
    page_size = 100
    target = request.args.get('target')
    view = request.args.get('view', None) or session.get('view_preference', 'list')
    fields_to_display = get_fitnessclub_listing_fields_for_entity(WORKOUT_ENTITY_NAME)
    filter_terms = get_filter_terms_from_request()
    entities = get_entities(WORKOUT_ENTITY_NAME, fields_to_display, filter_terms, member_id=member_id)
    entities = filter_entities_by_member_role(member_id, entities)

    return workouts_listing_base(
        context,
        WORKOUT_ENTITY_NAME,
        program_id,
        page,
        target,
        view,
        page_size,
        fields_to_display,
        target,
        filter_terms,
        entities,
        allow_multi_select=True,
        selected_entity_keys=[],
        modal_mode=True,
    )

def workouts_listing_base(context, entity_name, program_id, page, target, view, page_size, fields_to_display, div_id, filter_terms, entities, allow_multi_select=False, selected_entity_keys=None, modal_mode=False):
    total_pages = (len(entities) + page_size - 1) // page_size
    start = (page - 1) * page_size
    end = start + page_size
    current = entities[start:end]
    selected_entity_keys = selected_entity_keys or []

    if request.headers.get('HX-Target') == 'results-area':
        template_file_name = 'entity_results_partial.html'
    else:
        template_file_name = 'entity_list_component.html'

    # Set results_target_container based on target parameter
    results_target_container = target if target else 'results-area'
    entities_listing_route = f'/program/workouts-listing?entity_table={entity_name}&target={target}&program_id={program_id}'
    if allow_multi_select:
        entities_listing_route += '&allow_multi_select=true'

    if allow_multi_select:
        entity_action_route = None
        entity_action_route_method = None
        entity_action_route_target = None
    else:
        entity_action_route = f'/program/builder/{program_id}/add?entity_table={entity_name}'
        entity_action_route_method = 'post'
        entity_action_route_target = 'program-canvas'

    template_data = dict(
        title="Workouts Library",
        fields_to_display=fields_to_display,
        main_content_container='xyz',
        entities=current,
        entity_name=entity_name,
        filter_terms=filter_terms,
        args=request.args,
        page=page,
        view=view,
        total_pages=total_pages,
        entities_listing_route=entities_listing_route,
        entity_view_route=f'/workouts/viewer/workout?entity_table={entity_name}',
        entity_action_route=entity_action_route,
        entity_action_route_method=entity_action_route_method,
        entity_action_route_target=entity_action_route_target,
        entity_action_icon='bi-plus',
        entity_action_label='Add Workout',
        favorite_toggle_route='/admin/toggle-favorite',
        results_target_container=results_target_container,
        entity_card_view_html='workout_card_view.html',
        allow_multi_select=allow_multi_select,
        selected_entity_keys=selected_entity_keys,
        multi_select_checkbox_name='selected_entity_keys',
        multi_select_post_route=url_for('program.add_multiple_workouts', program_id=program_id) if allow_multi_select else None,
        multi_select_button_label='Add Selected Workouts',
        multi_select_button_icon='bi-plus-circle',
        modal_mode=modal_mode,
        context=context,
    )

    # displays workouts at the top level
    if modal_mode:
        return hx_render_template('workouts_listing_modal.html', **template_data)

    return hx_render_template(template_file_name, **template_data)


# def _build_program_workout_copy(source_workout, current_program, order_index):
#     copied_workout = source_workout.copy()
#     copied_workout['id'] = str(uuid.uuid4())
#     copied_workout['member_program_id'] = current_program['id']
#     copied_workout['order_index'] = order_index

#     workout_copy = MemberWorkoutDefinitionEntity(copied_workout)
#     workout_copy['key'] = workout_copy.get_composite_key()
#     workout_copy['key_str'] = '|'.join(workout_copy.get_composite_key())
#     return workout_copy

def new_program(name='new-workout-program', member_id=None):
    program_id = str(uuid.uuid4())
    return {
        'id': program_id,
        'created_by': member_id,
        'assigned_to_member_id': member_id,
        'name': name,
        'start_date': None,
        'end_date': None
    }

@bp.route('/builder/new')
@auth.login_required
def builder_new(context=None):
    member_id = get_member_id_from_user_context(context)
    if not member_id:
        abort(401)
    p = new_program(member_id=member_id)

    set_cache_value('current_program', p)
    delete_from_cache('current_program_workouts')
    delete_from_cache('workouts_to_remove')
    return redirect(url_for('program.builder'))

@bp.route('/edit')
@auth.login_required
def edit_program_details(context=None):
    es = EntityStore()

    composite_key_str = request.args.get('key', None)
    composite_key = eval(composite_key_str) if composite_key_str else None
    eoclass = EntityObject.get_entity_class_from_table_name(PROGRAM_ENTITY_NAME)
    program = eoclass(es.get_item_by_composite_key(composite_key))
    
    set_cache_value('current_program', program)
    delete_from_cache('current_program_workouts')
    delete_from_cache('workouts_to_remove')
    return redirect(url_for('program.builder'))

# ── Main Builder View ─────────────────────────────────────────────
@bp.route('/builder')
@auth.login_required
def builder(context=None):
    current_program = get_cache_value('current_program')
    if current_program:
        member_id = get_member_id_from_user_context(context)
        if not member_id:
            abort(401)
            
        # Get accessible members for coaches to assign programs to
        accessible_members = get_accessible_members_for_context(member_id)
        
        # Get role context for template conditional rendering
        from common.fitness.roles_service import get_member_role_context
        role_context = get_member_role_context(member_id)
        
        # Debug: Check program member_id and accessible members
        print(f"DEBUG - Program member_id: {current_program.get('member_id')} (type: {type(current_program.get('member_id'))})")
        print(f"DEBUG - Accessible members: {[(m.get('id'), m.get('name')) for m in accessible_members]}")
        print(f"DEBUG - Member IDs types: {[type(m.get('id')) for m in accessible_members]}")
        
        return hx_render_template('program_builder.html', 
                                program=current_program, 
                                accessible_members=accessible_members,
                                role_context=role_context,
                                context=context)
    abort(404)

@bp.route('/builder/<program_id>/canvas')
@auth.login_required
def program_canvas(context=None, program_id=None):
    return program_workouts_canvas(context, program_id)

def program_workouts_canvas(context=None, program_id=None):
    p = get_cache_value('current_program')
    if p:
        # we only want to populate the current_program_workouts cache the first time
        # we check the current_program_workouts cache for this.  It can be empty for a few reasons
        # 1) we have not populated it yet - this is the first time we are loading the builder view for this program, and
        # 2) we have populated it, but there are no workouts for this program yet - this could be the case if we just created a new program and have not added any workouts to it yet
        # 3) it was previously populated, but we deleted all the workouts using the program builder.  In this case, the workouts that we removed will be in the workouts_to_remove cache,
        # and we will check that when we load the workouts for the program.  If there are workouts in the workouts_to_remove cache, we know that the current_program_workouts cache is empty because 
        # we removed all the workouts from it, so we will not populate it with an empty list - instead, we will just leave it as is (empty) until we add new workouts to the program.  
        # 
        if not get_cache_value('current_program_workouts') and not get_cache_value('workouts_to_remove'):
            # get the workouts from the program
            workouts_list = get_workouts_from_program(p)
            for wk in workouts_list:
                wk['key'] = wk.get_composite_key()
                wk['key_str'] = '|'.join(wk.get_composite_key())
                # Ensure default values for new fields to support existing workouts
                if 'workout_type' not in wk or wk.get('workout_type') is None:
                    wk['workout_type'] = 'standard'
                if 'purpose' not in wk or wk.get('purpose') is None:
                    wk['purpose'] = ''
            # store the workouts in the cache as well
            set_cache_value('current_program_workouts', workouts_list)
        else:
            workouts_list = get_cache_value('current_program_workouts')

        if p['id'] == program_id:
            return hx_render_template('_program_workouts.html',
                                        program=p,
                                        workouts=workouts_list,
                                        context=context)
    abort(404)


@bp.route("/viewer/workout2/<workout_id>")
@auth.login_required
def view_workout2(context=None, workout_id=None):
    es = EntityStore()
    member_id = get_member_id_from_user_context(context)
    if not member_id:
        abort(401)
    workout_key_str = request.args.get('workout_key_str', None)
    workout_composite_key = workout_key_str.split('|')
    workout = es.get_item_by_composite_key(workout_composite_key)
    workout_definition_key = workout.get_composite_key() if workout else None

    current_program_workouts = get_cache_value('current_program_workouts')
    workout = next((wk for wk in current_program_workouts if wk.get('id', None) == workout_id), None)
    
    if not workout:
        abort(404)
    
    program_id = request.args.get('program_id', None)

    wrkout_exercises = get_exercises_from_workout(workout)
    exercises = { ex.get('id', None): ex for ex in wrkout_exercises }

    workout_sections = workout['workout_sections']
    
    return render_template(
        "workout_view2.html",
        program=None,  # No program context in this view
        workout=workout,
        exercises=exercises,
        workout_sections=workout_sections,
        workout_definition_key=workout_definition_key if workout_definition_key else workout.get('id',None),
        program_id=program_id,
        member_id=member_id
    )
@bp.route('/update_param_in_cache/<workout_id>', methods=['POST'])
@auth.login_required
def update_param_in_cache(context=None, workout_id=None):

    workouts = get_cache_value('current_program_workouts')
    # get workout from the list that has id matching workout_id
    current_workout = next((wk for wk in workouts if wk.get('id', None) == workout_id), None)
    if not current_workout:
        abort(404)

    exid  = request.form['exercise_id']
    param = request.form['param']
    value = request.form['value'] or None
    for s in current_workout['workout_sections']:
        for it in s['exercises']:
            if it['id']==exid:
                it['parameters'][param] = value

    set_cache_value('current_program_workouts', workouts)

    # w = get_cache_value('current_workout')
    # exid  = request.form['exercise_id']
    # workout_id = request.form['workout_id']
    # param = request.form['param']
    # value = request.form['value'] or None

    # for s in w[WORKOUT_SECTIONS]:
    #     for it in s['exercises']:
    #         if it['id']==exid:
    #             it['parameters'][param] = value

    # set_cache_value('current_workout', w)

    return ('', 204)


## this route does not appear to be used anymore
## - but the basic idea is to get the workout from the current_program_workouts cache, update the parameter value, then save back to cache
##
@bp.route('/builder/<workout_id>/update_param', methods=['POST'])
@auth.login_required
def update_param(context=None, workout_id=None):

    workouts = get_cache_value('current_program_workouts')
    # get workout from the list that has id matching workout_id
    current_workout = next((wk for wk in workouts if wk.get('id', None) == workout_id), None)
    if not current_workout:
        abort(404)

    exid  = request.form['exercise_id']

    program_id = request.form.get('program_id', None)
    param = request.form['param']
    value = request.form['value'] or None
    for s in current_workout['workout_sections']:
        for it in s['exercises']:
            if it['id']==exid:
                it['parameters'][param] = value

    # workouts[workout_id] = current_workout
    set_cache_value('current_program_workouts', workouts)

    return ('', 204)


@bp.route('/builder/<program_id>/reorder', methods=['POST'])
@auth.login_required
def reorder_workouts(context=None, program_id=None):
    w = get_cache_value('current_program_workouts')

    order = request.form.getlist('order[]')
    lookup = {it['id']:it for it in w}
    reordered_workout_list = [lookup[i] for i in order if i in lookup]

    # here we save the program to the cache
    set_cache_value('current_program_workouts', reordered_workout_list)

    return program_workouts_canvas(context, program_id)

@bp.route('/builder/<program_id>/updatename', methods=['POST'])
@auth.login_required
def update_program_name(context=None, program_id=None):

    # retrieve the workut from caache
    p = get_cache_value('current_program')
    
    p['name'] = request.form['name']

    set_cache_value('current_program', p)
    return program_workouts_canvas(context, program_id)

@bp.route('/builder/<program_id>/updatedate/<date_type>', methods=['POST'])
@auth.login_required
def update_dates(context=None, program_id=None, date_type=None):

    p = get_cache_value('current_program')
    
    if date_type not in ['start', 'end']:
        abort(400, description="Invalid date type. Must be 'start' or 'end'.")
    if date_type == 'start':
        p['start_date'] = request.form['start_date']
    else:
        p['end_date'] = request.form['end_date']

    set_cache_value('current_program', p)
    
    response = make_response('', 200)
    return response

@bp.route('/builder/<program_id>/update_assigned_member', methods=['POST'])
@auth.login_required
def update_assigned_member(context=None, program_id=None):
    member_id = get_member_id_from_user_context(context)
    if not member_id:
        abort(401)
        
    p = get_cache_value('current_program')
    if not p:
        abort(404)
        
    # Keep member_id as the creator/owner. Update assignment separately.
    assigned_member_id = request.form['assigned_member_id']
    p['assigned_to_member_id'] = assigned_member_id
    
    set_cache_value('current_program', p)

    response = make_response('', 200)
    return response

@bp.route('/builder/updateworkoutname/<workout_id>', methods=['POST'])
@auth.login_required
def update_workout_name(context=None, program_id=None, workout_id=None):

    current_program_workouts = get_cache_value('current_program_workouts')

    workout_name = request.form.get('workout_name', '')
    workout_type = request.form.get('workout_type', 'standard')
    purpose = request.form.get('purpose', '')

    # find the workout in the current_program_workouts list that has an id matching workout_id
    workout = next((wk for wk in current_program_workouts if wk.get('id', None) == workout_id), None)
    
    if not workout:
        abort(404)

    # set the new values
    workout['name'] = workout_name
    workout['workout_type'] = workout_type
    workout['purpose'] = purpose

    # current_program_workouts[workout_id] = workout
    set_cache_value('current_program_workouts', current_program_workouts)
    
    response = make_response('', 200)
    return response

@bp.route('/builder/<program_id>/save', methods=['POST'])
@auth.login_required
def save_program(context=None, program_id=None):
    member_id = get_member_id_from_user_context(context)
    if not member_id:
        abort(401)    

    current_program = get_cache_value('current_program')
    if current_program:
        if current_program['id'] != program_id:
            abort(404)

    es = EntityStore()

    workouts_in_program = []
    current_program_workouts = get_cache_value('current_program_workouts')
    i = 0
    for w in current_program_workouts:
        w['order_index'] = i
        i += 1
        workouts_in_program.append(MemberWorkoutDefinitionEntity(w))

    # handle workouts that were removed from the program
    workouts_to_remove = get_cache_value('workouts_to_remove') or []

    for wtr in workouts_to_remove:
        # es.delete_item(MemberWorkoutDefinitionEntity(wtr))
        if wtr.get('member_program_id') == current_program['id']:
            wtr['member_program_id'] = None  # unlink the workouts from the program
        es.upsert_item(MemberWorkoutDefinitionEntity(wtr))
    
    es.upsert_items(workouts_in_program)
    es.upsert_item(MemberProgramsEntity(current_program))

    delete_from_cache('current_program')
    delete_from_cache('current_program_workouts')
    delete_from_cache('workouts_to_remove')

    member_id = get_member_id_from_user_context(context)
    if not member_id:
        abort(401)
    response = make_response(programs_listing2(context))
    response.headers['HX-Trigger'] = json.dumps({
        "eventListChanged": { "target": "body" },
            "showMessage": { 
            "target": "body",
            "value": "program saved." }
        })
    return response

@bp.route('/builder/<program_id>/cancel', methods=['POST'])
@auth.login_required
def cancel_editing_program(context=None, program_id=None):
    member_id = get_member_id_from_user_context(context)
    if not member_id:
        abort(401)    

    current_program = get_cache_value('current_program')
    if current_program:
        if current_program['id'] != program_id:
            abort(404)

    es = EntityStore()


    delete_from_cache('current_program')
    delete_from_cache('current_program_workouts')
    delete_from_cache('workouts_to_remove')


    response = make_response(programs_listing2(context))
    response.headers['HX-Trigger'] = json.dumps({
        "eventListChanged": { "target": "body" },
            "showMessage": { 
            "target": "body",
            "value": "program editing canceled." }
        })
    return response

@bp.route('/builder/<program_id>/delete', methods=['POST'])
@auth.login_required
def delete_program(context=None, program_id=None):
    member_id = get_member_id_from_user_context(context)
    if not member_id:
        abort(401)

    current_program = get_cache_value('current_program')
    if current_program:
        if current_program['id'] != program_id:
            abort(404)

    es = EntityStore()
    workouts_in_program = []
    current_program_workouts = get_cache_value('current_program_workouts')

    for w in current_program_workouts:
        w['member_program_id'] = None   # unlink the workouts from the program
        workouts_in_program.append(MemberWorkoutDefinitionEntity(w))
    es.upsert_items(workouts_in_program)

    # handle workouts that were removed from the program
    workouts_to_remove = get_cache_value('workouts_to_remove') or []

    for wtr in workouts_to_remove:
        es.upsert_item(MemberWorkoutDefinitionEntity(wtr))

    es.delete_item(MemberProgramsEntity(current_program))

    delete_from_cache('current_program')
    delete_from_cache('current_program_workouts')
    delete_from_cache('workouts_to_remove')

    # delete from the in-memory entity cache
    delete_entity(MemberProgramsEntity(current_program))

    response = make_response(programs_listing2(context))
    response.headers['HX-Trigger'] = json.dumps({
        "eventListChanged": { "target": "body" },
            "showMessage": { 
            "target": "body",
            "value": "program deleted." }
        })
    return response


@bp.route('/builder/<program_id>/save_copy', methods=['POST'])
@auth.login_required
def save_copy_of_program(context=None, program_id=None):

    # this method is similar to save_program, but we create a copy of the program with a new id
    # we also need to create copies of the workouts in the program with new ids
    # each copied workout also needs to reference the new program id

    member_id = get_member_id_from_user_context(context)
    if not member_id:
        abort(401)    

    current_program = get_cache_value('current_program')
    if current_program:
        if current_program['id'] != program_id:
            abort(404)

    es = EntityStore()

    # create a copy of the program with a new id
    new_program_id = str(uuid.uuid4())
    current_program['id'] = new_program_id
    current_program['name'] = f"{current_program['name']} (copy)"
    current_program['member_id'] = member_id
    current_program['assigned_to_member_id'] = member_id
    current_program['created_by'] = member_id

    workouts_in_program = []
    current_program_workouts = get_cache_value('current_program_workouts')
    i = 0
    for w in current_program_workouts:
        w['order_index'] = i
        i += 1
        # create a copy of the workout with a new id
        new_workout_id = str(uuid.uuid4())
        w['id'] = new_workout_id
        w['member_program_id'] = new_program_id
        w['member_id'] = member_id
        w['created_by'] = member_id

        workouts_in_program.append(MemberWorkoutDefinitionEntity(w))

    # handle workouts that were removed from the program
    workouts_to_remove = get_cache_value('workouts_to_remove') or []

    for wtr in workouts_to_remove:
        es.delete_item(MemberWorkoutDefinitionEntity(wtr))

    es.upsert_items(workouts_in_program)
    es.upsert_item(MemberProgramsEntity(current_program))

    delete_from_cache('current_program')
    delete_from_cache('current_program_workouts')
    delete_from_cache('workouts_to_remove')


    member_id = get_member_id_from_user_context(context)
    if not member_id:
        abort(401)
    
    response = make_response(programs_listing2(context))
    response.headers['HX-Trigger'] = json.dumps({
        "eventListChanged": { "target": "body" },
            "showMessage": { 
            "target": "body",
            "value": "copy of program saved." }
        })
    return response

# this is called when you click the edit button on a workout in the program builder canvas 
# - it loads the workout into the workout editor and sets a cache value to keep track of which workout we are editing 
# so that when we save the workout, we can update the correct workout in the current_program_workouts cache
@bp.route('/builder/<program_id>/edit', methods=['POST'])
@auth.login_required
def edit_workout(context=None, program_id=None):

    current_program_workouts = get_cache_value('current_program_workouts')
    wk_id = request.form['workout_id']

    # we need to keep track of the workout that is being removed so we can unlink it from the program when we save the program
    # so first find the workout to unlink from the program
    workout_to_edit = next((wk for wk in current_program_workouts if wk.get('id', None) == wk_id), None)
    set_cache_value('workout_editor_context', { 'editing_program_workout': workout_to_edit,
                                                'program_id': program_id } )
    return bring_up_workouts_builder(workout_to_edit)


@bp.route('/builder/<program_id>/remove', methods=['POST'])
@auth.login_required
def remove_workout(context=None, program_id=None):

    current_program_workouts = get_cache_value('current_program_workouts')
    wk_id = request.form['workout_id']

    # we need to keep track of the workout that is being removed so we can unlink it from the program when we save the program
    # so first find the workout to unlink from the program
    workout_to_unlink = next((wk for wk in current_program_workouts if wk.get('id', None) == wk_id), None)
    workout_to_unlink['member_program_id'] = None  # unlink from program

    # now remove that workout from the current_program_workouts list
    current_program_workouts = [it for it in current_program_workouts if it['id']!=wk_id]

    workouts_to_remove = get_cache_value('workouts_to_remove') or []
    workouts_to_remove.append(workout_to_unlink)
    set_cache_value('workouts_to_remove', workouts_to_remove)

    set_cache_value('current_program_workouts', current_program_workouts)

    return program_workouts_canvas(context, program_id)


@bp.route('/builder/<program_id>/add', methods=['POST'])
@auth.login_required
def add_workout(context=None, program_id=None):

    current_program = get_cache_value('current_program')
    current_program_workouts = get_cache_value('current_program_workouts')
    num_workouts = len(current_program_workouts) if current_program_workouts else 0
    if current_program:
        if current_program['id'] != program_id:
            abort(404)

    composite_key_str = request.args.get('key', None)
    composite_key = eval(composite_key_str) if composite_key_str else None

    added_workout = EntityStore().get_item_by_composite_key(composite_key)
    if not added_workout:
        abort(404)

    # workout_copy = _build_program_workout_copy(added_workout, current_program, num_workouts)
    # only allow a workout to be added if it not already a part of another program
    # check if the added_workout has a member_program_id that is not None
    if added_workout.get('member_program_id', None) is not None:
        response = make_response('')
        response.headers['HX-Trigger'] = json.dumps({
            "refreshProgramCanvas": {"target": "body"},
            "showMessage": {"target": "body", "value": "Workout is already part of another program and cannot be added."}
        })
        return response
    else:
        added_workout['member_program_id'] = current_program['id']
        current_program_workouts.append(added_workout)

    # update the cache
    set_cache_value('current_program', current_program)
    set_cache_value('current_program_workouts', current_program_workouts)

    return program_workouts_canvas(context, program_id)


@bp.route('/builder/<program_id>/add-multiple', methods=['POST'])
@auth.login_required
def add_multiple_workouts(context=None, program_id=None):
    current_program = get_cache_value('current_program')
    if not current_program or current_program.get('id') != program_id:
        abort(404)

    current_program_workouts = get_cache_value('current_program_workouts') or []
    selected_keys = list(dict.fromkeys([key for key in request.form.getlist('selected_entity_keys') if key]))

    if not selected_keys:
        response = make_response('')
        response.headers['HX-Trigger'] = json.dumps({
            "refreshProgramCanvas": {"target": "body"},
            "showMessage": {"target": "body", "value": "No workouts selected."}
        })
        return response

    added_count = 0
    es = EntityStore()
    errmsg = ""
    for composite_key_str in selected_keys:
        try:
            composite_key = literal_eval(composite_key_str)
        except (ValueError, SyntaxError):
            continue

        source_workout = es.get_item_by_composite_key(composite_key)
        if not source_workout:
            continue
        # only allow a workout to be added if it not already a part of another program
        # check if the added_workout has a member_program_id that is not None
        if source_workout.get('member_program_id', None) is not None:
            response = make_response('')
            response.headers['HX-Trigger'] = json.dumps({
                "refreshProgramCanvas": {"target": "body"},
                "showMessage": {"target": "body", "value": "Workout is already part of another program and cannot be added."}
            })
            errmsg += f"could not add workout \"{source_workout.get('name', 'unknown')}\" because it is already part of another program."
            continue
        else:
            source_workout['member_program_id'] = current_program['id']
            current_program_workouts.append(source_workout)

        # workout_copy = _build_program_workout_copy(source_workout, current_program, len(current_program_workouts))
        # current_program_workouts.append(workout_copy)
        added_count += 1

    set_cache_value('current_program_workouts', current_program_workouts)
    session.pop(PROGRAM_MULTI_SELECT_SESSION_KEY, None)

    response = make_response('')
    response.headers['HX-Trigger'] = json.dumps({
        "refreshProgramCanvas": {"target": "body"},
        "showMessage": {"target": "body", "value": f"Added {added_count} workout(s). {errmsg}"}
    })
    return response


@bp.route('/start_workout', methods=['POST'])
@auth.login_required
def start_workout(context=None):
    member_id = get_member_id_from_user_context(context)
    short_name = get_user_profile(member_id).get('short_name', None)

    scheduled_workout_event_id = request.form.get('scheduled_workout_event_id', None)

    # If no event ID provided, create a new scheduled event (adhoc workout)
    if not scheduled_workout_event_id:
        calendar_service = get_calendar_service()
        current_date = datetime.now().date().strftime("%Y-%m-%d")
        current_time = datetime.now().time().strftime("%H:%M")
        scheduled_workout_event_id = calendar_service.add_workout_event(
            member_short_name=short_name,
            event_date=current_date, 
            event_time=current_time,
            location="YMCA", 
            metadata=f'#id={member_id}'
        )
        is_adhoc_workout = True
    else:
        is_adhoc_workout = False


    workout_key_str = request.form.get('workout_key', None)
    workout_key = eval(workout_key_str) if workout_key_str else None
    workout = EntityStore().get_item_by_composite_key(workout_key) if workout_key else None

    program_composite_key_str = request.form.get('program_key', None)
    program_composite_key = eval(program_composite_key_str) if program_composite_key_str else None

    

    workout_instance, exercises, program_entity, workout_instance_key, adjustments = _start_workout_logic(workout_key_str, 
                                                                                                          program_composite_key_str, 
                                                                                                          scheduled_workout_event_id,
                                                                                                          member_id,
                                                                                                          is_adhoc_workout=is_adhoc_workout)
  
    last = session.get(f"last_section_{workout_instance['id']}")  # no fallback
    
    # Get current workout state to see if there are any parameter overrides
    current_workout_state = get_active_workout_state()
    workout_started_ts = current_workout_state.get('time_workout_started', None) if current_workout_state else None
    current_parameters = {}
    if current_workout_state:
        current_parameters = current_workout_state.get('exercise_parameters', {})
    workout_sections = workout_instance['workout_sections']
    
    workout_sections = [s for s in workout_sections if len(s.get('exercises', [])) > 0]
    if not last:
        for section in workout_sections:
            if len(section.get('exercises', [])) > 0:
                last = section.get('name', None)
                break

    last_exercise_indexes_by_section = {
        section.get('name'): session.get(f"last_exercise_index_{workout_instance.get('id')}_{section.get('name')}")
        for section in workout_sections
    }

    workout_view_preference = session.get('workout_view_preference', 'accordion')
    return render_template(
        "workout_view.html",
        workout=workout_instance,
        workout_sections=workout_sections,
        exercises=exercises,
        current_parameters=current_parameters,
        default_section=last,
        last_exercise_indexes_by_section=last_exercise_indexes_by_section,
        program=program_entity,
        program_key=program_composite_key,
        workout_instance_key=workout_instance_key,
        scheduled_workout_event_id=scheduled_workout_event_id,
        finish_workout_url=url_for('program.finish_workout', workout_instance_key=workout_instance_key),
        cancel_workout_url=url_for('program.cancel_workout', workout_instance_key=workout_instance_key),
        show_finish_button=True,
        time_workout_started=workout_started_ts,
        active_workout=True,
        workout_view_preference=workout_view_preference,
        rs=rm_spaces
    )

def _start_workout_logic(workout_key, program_key, scheduled_workout_event_id, member_id, is_adhoc_workout=False):
    """
    Encapsulates the logic for starting a workout, including copying the workout,
    updating the program, and setting the session state.
    """
    es = EntityStore()
    workout_composite_key = eval(workout_key) if workout_key else None
    program_composite_key = eval(program_key) if program_key else None

    workout_entity = es.get_item_by_composite_key(workout_composite_key) if workout_composite_key else None
    program_entity = es.get_item_by_composite_key(program_composite_key) if program_composite_key else None

    workout_def_id = workout_entity.get('id', None) if workout_entity else None

    workout_instance = MemberWorkoutInstanceEntity(workout_entity.copy()) if workout_entity else MemberWorkoutInstanceEntity({})

    workout_instance.update({
        'id': str(uuid.uuid4()),
        'member_id': member_id,
        'started_ts': datetime.now().isoformat(),
        'finished_ts': "",
        'scheduled_workout_event_id': scheduled_workout_event_id,
        'member_workout_def_id': workout_entity['id'] if workout_entity else None,
        'member_program_id': program_entity['id'] if program_entity else None,
        'member_program_name': program_entity.get('name', '') if program_entity else '',
        'name': workout_entity.get('name', 'Unnamed Workout') if workout_entity else 'Unnamed Workout'
    })
    es.upsert_item(workout_instance)
    workout_instance_key = workout_instance.get_composite_key()

    wrkout_exercises = get_exercises_from_workout(workout_instance)
    exercises = {ex.get('id', None): ex for ex in wrkout_exercises}

    initialize_active_workout_state(workout_instance_key, program_key, scheduled_workout_event_id, is_adhoc_workout=is_adhoc_workout)
    adjustments = {}
    return workout_instance, exercises, program_entity, workout_instance_key, adjustments

   
@bp.route('/finish_workout/<workout_instance_key>', methods=['POST'])
@auth.login_required
def finish_workout(context=None, workout_instance_key=None):

    current_workout_state = get_active_workout_state()
    if not current_workout_state:
        abort(404)
    current_workout_state['state'] = 'finishing_workout'
    update_active_workout_state(current_workout_state)
    return redirect('/')

@bp.route('/really_finish_workout/<workout_instance_key>', methods=['POST'])
@auth.login_required
def really_finish_workout(context=None, workout_instance_key=None):

    es = EntityStore()
    workout_composite_key = eval(workout_instance_key) if workout_instance_key else None
    workout_instance = es.get_item_by_composite_key(workout_composite_key)

    # program_composite_key_str = request.form.get('program_key', None)
    # program_composite_key = eval(program_composite_key_str) if program_composite_key_str else None
    # program_entity = es.get_item_by_composite_key(program_composite_key)
    
    # post to the google calendar service that the workout is finished
    scheduled_workout_event_id = request.form.get('scheduled_workout_event_id', None)
    started_ts = request.form.get('started_ts', None)
    finished_ts = request.form.get('finished_ts', None)
    member_feedback = request.form.get('member_feedback', '')
    next_time_strategy = request.form.get('next_time_strategy', 'custom')

    current_workout_state = get_active_workout_state()
    adjustments_for_next_workout = current_workout_state.get('adjustments', {})
    exercise_parameters = current_workout_state.get('exercise_parameters', {})

    original_parameters = {}
    for section in workout_instance.get('workout_sections', []):
        for exercise in section.get('exercises', []):
            exercise_id = exercise.get('id', None)
            if exercise_id:
                original_parameters[exercise_id] = exercise.get('parameters', {}).copy()

    # here we want to update the parameters of the exercises in the workout instance
    # with the parameters from the current workout state
    
    for exercise, params in exercise_parameters.items():
        for section in workout_instance.get('workout_sections', []):
            for ex in section.get('exercises', []):
                if ex.get('id', None) == exercise:
                    # here I want to update the parameters of the exercise with the params from the current workout state
                    for k, v in params.items():
                        ex['parameters'][k] = v

    # if the strategy is original, then we don't need to update the memberWorkoutDefinition with the adjustments_for_next_workout, as next time we will just use the original parameters

    if next_time_strategy == 'original':
        updated_parameters = None
    # otherwise, if the strategy is performed_today, then we want to use the parameters from the current workout state as the adjustments for next time
    # we will update the memberWorkoutDefinition with the adjustments_for_next_workout, so that next time we will use these parameters
    elif next_time_strategy == 'performed_today':
        updated_parameters = exercise_parameters
    else:
        updated_parameters = adjustments_for_next_workout if adjustments_for_next_workout else exercise_parameters
    
    # get the member workout definition for this workout instance, and update the parameters of the exercises with the updated_parameters, but only if the updated_parameters is not None
    if updated_parameters:
        member_workout_def_id = workout_instance.get('member_workout_def_id', None)
        member_id = workout_instance.get('member_id', None)
        workout_definition = es.get_item(MemberWorkoutDefinitionEntity({'id': member_workout_def_id}))
        for section in workout_definition.get('workout_sections', []):
            for exercise in section.get('exercises', []):
                exercise_id = exercise.get('id', None)
                if exercise_id and exercise_id in updated_parameters:
                    adjustment = updated_parameters[exercise_id]
                    exercise['parameters'].update(adjustment)
        es.upsert_item(workout_definition)

    workout_instance['started_ts'] = _normalize_form_datetime(started_ts, workout_instance.get('started_ts'))
    workout_instance['finished_ts'] = _normalize_form_datetime(finished_ts, datetime.now().isoformat())
    workout_instance['member_feedback'] = member_feedback.strip()
    es.upsert_item(workout_instance)
    
    # store the parameters of the current workout exercises away 
    extract_and_load_exercise_events_from_workout_instance(workout_instance)

    clear_active_workout_state()
    # session.pop('current_workout_instance_state', None)
    session.pop(f"last_section_{workout_instance['id']}", None)

    cal = get_calendar_service()
    cal.update_status_of_workout_event(scheduled_workout_event_id, 'done')

    return redirect('/')

@bp.route('/continue_workout/<workout_instance_key>', methods=['POST'])
@auth.login_required
def continue_workout(context=None, workout_instance_key=None):
    current_workout_state = get_active_workout_state()
    if not current_workout_state:
        abort(404)
    current_workout_state['state'] = 'workout_started'
    update_active_workout_state(current_workout_state)
    return redirect('/')

@bp.route('/cancel_workout/<workout_instance_key>', methods=['POST'])
@auth.login_required
def cancel_workout(context=None, workout_instance_key=None):

    # this method is called when a user accidentally starts a workout
    # and wants to cancel it before finishing it
    # it will remove the entities that were created when the workout was started
    # and redirect to the home page
    
    es = EntityStore()
    workout_instance_composite_key = eval(workout_instance_key) if workout_instance_key else None
    workout_instance = es.get_item_by_composite_key(workout_instance_composite_key)
    if not workout_instance:
        abort(404)

    # check if the workout instance is adhoc or scheduled
    workout_state = get_active_workout_state()
    if workout_state and workout_state.get('is_adhoc_workout', False):
        # if it is an adhoc workout, we need to delete the calendar event that was created for it
        scheduled_workout_event_id = workout_instance.get('scheduled_workout_event_id', None)
        if scheduled_workout_event_id:
            cal = get_calendar_service()
            cal.delete_workout_event(scheduled_workout_event_id)
            
    # clear the 'current_workout_instance_state' from the session
    clear_active_workout_state()
    # session.pop('current_workout_instance_state', None)
    session.pop(f"last_section_{workout_instance['id']}", None)

    # remove the workout_instance from the entity store
    es.delete_item(workout_instance)

    return redirect('/', 302)

