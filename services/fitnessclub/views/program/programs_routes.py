from datetime import datetime
import json

import uuid
from flask import Blueprint, abort, current_app, make_response, redirect, render_template, request, session, url_for
from common.entity_store import EntityObject, EntityStore
from common.fitness.active_fitness_registry import _get_filter_terms_from_request, get_fitnessclub_listing_fields_for_entity
from common.fitness.cacher import delete_from_cache, get_cache_value, set_cache_value
from common.fitness.entities_getter import get_entity, get_entities
from common.fitness.entity_constants import PROGRAM_ENTITY_NAME, WORKOUT_ENTITY_NAME
from common.fitness.get_calendar_service import get_calendar_service
from common.fitness.hx_common import hx_render_template
from common.fitness.hx_common import rm_spaces
from common.fitness.member_entity import MembershipRegistry, get_member_detail_from_user_context
from common.fitness.member_program_entity import MemberProgramEntity
from common.fitness.member_workout_entity import MemberWorkoutDefinitionEntity, MemberWorkoutInstanceEntity, get_exercises_from_workout
from common.fitness.workout_state import clear_active_workout_state, get_active_workout_state, initialize_active_workout_state
bp = Blueprint('program', __name__, template_folder='templates')
from auth import auth

@bp.route('/')
@auth.login_required
def index(context=None):
    return redirect(url_for('program.programs_listing'), 302)

@bp.route('/programs-listing', methods=['GET', 'POST'])
@auth.login_required
def programs_listing(context=None):

    entity_name = PROGRAM_ENTITY_NAME
    page = int(request.args.get('page', 1))
    page_size = 100
    member_id = get_member_detail_from_user_context(context).get('id', None)
    if not member_id:
        abort(401)
    # Handle view preference
    view = (request.form.get('view') if request.method == 'POST' 
            else request.args.get('view')) or session.get('view_preference', 'list')
    
    if view != session.get('view_preference'):
        session['view_preference'] = view
    
    fields_to_display = get_fitnessclub_listing_fields_for_entity(entity_name)
    filter_terms = _get_filter_terms_from_request()

    member = get_member_detail_from_user_context(context)
    entities = get_entities(entity_name, fields_to_display, filter_terms, partition_key=member.get('id', None), sort_by='end_date', sort_ascending=False, member_id=member_id)

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
    # displays workouts at the top level
    return hx_render_template(
        template_file_name,
        entity_name=entity_name,
        main_content_container="entities-container",        
        fields_to_display=fields_to_display,
        entities=current,
        filter_terms=filter_terms,
        args=request.args,
        page=page,
        view=view,
        entity_add_route=url_for('program.builder_new'),        
        total_pages=total_pages,
        entity_view_route=f'/program/viewer?entity_table={entity_name}',
        entities_listing_route=f'/program/programs-listing?entity_table={entity_name}',
        entity_action_route=f'/program/edit?entity_table={entity_name}',
        entity_action_icon='bi-pencil-square',  
        entity_action_label='Edit Program',       
        context=context)

@bp.route('/viewer')
@auth.login_required
def program_viewer(context=None):
    return hx_render_template(
        "program_viewer.html",
        entity_name=PROGRAM_ENTITY_NAME,
        main_content_container="entities-container",
        fields_to_display=['name', 'description', 'start_date', 'end_date', 'workouts'],
        args=request.args,
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
    member_id = get_member_detail_from_user_context(context).get('id', None)
    if not member_id:
        abort(401)
    # Handle view preference
    view = (request.form.get('view') if request.method == 'POST' 
            else request.args.get('view')) or session.get('view_preference', 'list')
    
    if view != session.get('view_preference'):
        session['view_preference'] = view
    
    fields_to_display = get_fitnessclub_listing_fields_for_entity(entity_name)
    filter_terms = _get_filter_terms_from_request()

    entities = get_entities(entity_name, fields_to_display, filter_terms, member_id=member_id)

    # mobile = request.args.get('mobile', type=bool, default=False)
    # div_id = 'lib-list-mobile' if mobile else 'lib-list'
    div_id = target
    current_program = get_cache_value('current_program')

    if current_program:
        if current_program['id'] != program_id:
            abort(404)
    else:
            abort(404)     

    entities = get_entities(entity_name, fields_to_display, filter_terms, member_id=member_id)
    return workouts_listing_base(context, entity_name, program_id, page, target, view, page_size, fields_to_display, div_id, filter_terms, entities)

def workouts_listing_base(context, entity_name, program_id, page, target, view, page_size, fields_to_display, div_id, filter_terms, entities):
    total_pages = (len(entities) + page_size - 1) // page_size
    start = (page - 1) * page_size
    end = start + page_size
    current = entities[start:end]

    if request.headers.get('HX-Target') == 'results-area':
        template_file_name = 'entity_results_partial.html'
    else:
        template_file_name = 'entity_list_component.html'

    # displays workouts at the top level
    return hx_render_template(
        template_file_name,
        fields_to_display=fields_to_display,
        main_content_container=div_id,        
        entities=current,
        entity_name=entity_name,
        filter_terms=filter_terms,
        args=request.args,
        page=page,
        view=view,
        total_pages=total_pages,
        entities_listing_route=f'/program/workouts-listing?entity_table={entity_name}&target={target}&program_id={program_id}',
        entity_view_route=f'/workouts/viewer/workout?entity_table={entity_name}',
        entity_action_route=f'/program/builder/{program_id}/add?entity_table={entity_name}',
        entity_action_route_method='post',
        entity_action_route_target="program-canvas",
        entity_action_icon='bi-plus',  
        entity_action_label='Add Workout',       
        context=context)

def new_program(name='new-workout-program', member_id=None):
    program_id = str(uuid.uuid4())
    return {
        'id': program_id,
        'member_id': member_id,
        'name': name,
        'start_date': None,
        'end_date': None
    }

@bp.route('/builder/new')
@auth.login_required
def builder_new(context=None):
    member = get_member_detail_from_user_context(context)
    p = new_program(member_id=member['id'])

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
        return hx_render_template('program_builder.html', program=current_program, context=context)
    abort(404)

@bp.route('/builder/<program_id>/canvas')
@auth.login_required
def program_canvas(context=None, program_id=None):
    return program_canvas2(context, program_id)

def program_canvas2(context=None, program_id=None):
    p = get_cache_value('current_program')
    if p:
        # we only want to populate the current_program_workouts cache the first time
        # if it is already populated, we will use that
        if not get_cache_value('current_program_workouts'):
            # get the workouts from the program
            program_workouts = get_workouts_from_program(p)
            # workouts_dict = { wk.get('id', None): wk for wk in program_workouts }
            workouts_list = program_workouts
            for wk in workouts_list:
                wk['key'] = wk.get_composite_key()
                wk['key_str'] = '|'.join(wk.get_composite_key())
            # store the workouts in the cache as well
            set_cache_value('current_program_workouts', workouts_list)
        else:
            workouts_list = get_cache_value('current_program_workouts')

        if p['id'] == program_id:
            return hx_render_template('_program_canvas2.html',
                                        program=p,
                                        workouts=workouts_list,
                                        context=context)
    abort(404)


@bp.route("/viewer/workout2/<workout_id>")
@auth.login_required
def view_workout2(context=None, workout_id=None):
    member_id = get_member_detail_from_user_context(context).get('id', None)

    current_program = get_cache_value('current_program')
    current_program_workouts = get_cache_value('current_program_workouts')
    
    # workout = current_program_workouts.get(workout_id, None)
    # find the workout in the current_program_workouts list that has an id matching workout_id
    workout = next((wk for wk in current_program_workouts if wk.get('id', None) == workout_id), None)
    
    if not workout:
        abort(404)

    # workout_key_pipe_delimited_str = request.args.get('keyStrPipeDelimited', None)
    # # Convert pipe-delimited string to a list
    # workout_composite_key = workout_key_pipe_delimited_str.split('|')
    # workout = EntityStore().get_item_by_composite_key2(workout_composite_key)
    # if not workout:
    #     abort(404)
    
    program_id = request.args.get('program_id', None)

    wrkout_exercises = get_exercises_from_workout(workout)
    exercises = { ex.get('id', None): ex for ex in wrkout_exercises }

    if 'workout_sections' in workout:
        workout_sections = workout['workout_sections']
    else:
        workout_sections = workout['sections']

    return render_template(
        "workout_view2.html",
        program=None,  # No program context in this view
        workout=workout,
        exercises=exercises,
        workout_sections=workout_sections,
        program_id=program_id,
        member_id=member_id
    )

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

    return program_canvas2(context, program_id)

@bp.route('/builder/<program_id>/updatename', methods=['POST'])
@auth.login_required
def update_program_name(context=None, program_id=None):

    # retrieve the workut from caache
    p = get_cache_value('current_program')
    
    p['name'] = request.form['name']

    set_cache_value('current_program', p)
    return program_canvas2(context, program_id)

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

@bp.route('/builder/updateworkoutname/<workout_id>', methods=['POST'])
@auth.login_required
def update_workout_name(context=None, program_id=None, workout_id=None):

    current_program_workouts = get_cache_value('current_program_workouts')

    workout_name = request.form.get('workout_name', '')

    # find the workout in the current_program_workouts list that has an id matching workout_id
    workout = next((wk for wk in current_program_workouts if wk.get('id', None) == workout_id), None)
    
    if not workout:
        abort(404)

    # set the new name
    workout['name'] = workout_name

    # current_program_workouts[workout_id] = workout
    set_cache_value('current_program_workouts', current_program_workouts)
    
    response = make_response('', 200)
    return response

def get_workouts_from_program(program):
    # in the 1.0 data model, the workouts are stored as embedded objects in the program
    # in the 2.0 data model, the workouts are stored as separate entities in the MemberWorkoutDefinitionTable, where 
    # those entities have a member_program_id field that references the program they belong to
    workouts = []

    es = EntityStore()
    # wondering here if we can use the EntityCache?  
    # TODO:  analyze if the cache is an eligible option
    mbr_workout_definitions = list(es.list_items(MemberWorkoutDefinitionEntity({"member_id": program['member_id']})))
    workouts = [w for w in mbr_workout_definitions if w.get('member_program_id', None)==program['id']]
    # sort workouts by order_index
    workouts = sorted(workouts, key=lambda x: x.get('order_index', 0))
    
    return workouts

@bp.route('/builder/<program_id>/save', methods=['POST'])
@auth.login_required
def save_program(context=None, program_id=None):
    member_id = get_member_detail_from_user_context(context).get('id', None)
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
        es.delete_item(MemberWorkoutDefinitionEntity(wtr))
    
    es.upsert_items(workouts_in_program)
    es.upsert_item(MemberProgramEntity(current_program))

    delete_from_cache('current_program')
    delete_from_cache('current_program_workouts')
    delete_from_cache('workouts_to_remove')

    response = make_response('')
    response.headers['HX-Trigger'] = json.dumps({
        "eventListChanged": { "target": "body" },
            "showMessage": { 
            "target": "body",
            "value": "program saved." }
        })
    response.headers['HX-Redirect'] = url_for('program.index')
    return response

@bp.route('/builder/<program_id>/save_copy', methods=['POST'])
@auth.login_required
def save_copy_of_program(context=None, program_id=None):

    # this method is similar to save_program, but we create a copy of the program with a new id
    # we also need to create copies of the workouts in the program with new ids
    # each copied workout also needs to reference the new program id

    member_id = get_member_detail_from_user_context(context).get('id', None)
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
    es.upsert_item(MemberProgramEntity(current_program))

    delete_from_cache('current_program')
    delete_from_cache('current_program_workouts')
    delete_from_cache('workouts_to_remove')

    response = make_response('')
    response.headers['HX-Trigger'] = json.dumps({
        "eventListChanged": { "target": "body" },
            "showMessage": { 
            "target": "body",
            "value": "copy of program saved." }
        })
    response.headers['HX-Redirect'] = url_for('program.index')
    return response


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

    return program_canvas2(context, program_id)


@bp.route('/builder/<program_id>/add', methods=['POST'])
@auth.login_required
def add_workout(context=None, program_id=None):

    current_program = get_cache_value('current_program')
    current_program_workouts = get_cache_value('current_program_workouts')
    num_workouts = len(current_program_workouts) if current_program_workouts else 0
    if current_program:
        if current_program['id'] != program_id:
            abort(404)

    # here we get the key of the workout from the query parameters
    # and we look it up in the workouts table
    # if it is not found we abort with a 404
    # if it is found we:
    # create a copy of the workout from the WorkoutTable and give it a new id
    # laster when we save the program, we will save the workout copy to the ProgramWorkoutTable
    # the workouts in the program.workouts list are from teh WorkoutTable
    # we will copy thos workout objects into the ProgramWorkoutTable, then use the id & Program_id of that copy to populate the program.workouts list

    composite_key_str = request.args.get('key', None)
    composite_key = eval(composite_key_str) if composite_key_str else None

    added_workout = EntityStore().get_item_by_composite_key(composite_key)
    if not added_workout:
        abort(404)

    added_workout_id = added_workout['id']
    added_workout['id'] = str(uuid.uuid4())  # generate a new id for the program workout
    added_workout['program_id'] = current_program['id']  # set the program id for the workout
    added_workout['base_workout_def_id'] = added_workout_id  # keep the original workout id for reference
    added_workout['member_id'] = current_program['member_id']  # set the member id for the workout
    added_workout['created_by'] = current_program['member_id']  # set the created by for the workout
    added_workout['member_program_id'] = current_program['id']  # set the member program id for the workout
    added_workout['order_index'] = num_workouts  # set the order index for the workout
    workout_copy = MemberWorkoutDefinitionEntity(added_workout)

    workout_copy['key'] = workout_copy.get_composite_key()
    workout_copy['key_str'] = '|'.join(workout_copy.get_composite_key())    

    # current_program['workouts'].append({'key': workout_copy.get_composite_key(), 'id':workout_copy['id'], "name": workout_copy['name']})
    # current_program_workouts[workout_copy['id']] = workout_copy
    # append to the current_program_workouts list
    current_program_workouts.append(workout_copy)

    # update the cache
    set_cache_value('current_program', current_program)
    set_cache_value('current_program_workouts', current_program_workouts)

    return program_canvas2(context, program_id)


@bp.route('/start_workout/<workout_key>', methods=['POST'])
@auth.login_required
def start_workout(context=None, workout_key=None):

    scheduled_workout_event_id = request.form.get('scheduled_workout_event_id', None)
    workout_composite_key = eval(workout_key) if workout_key else None

    program_composite_key_str = request.form.get('program_key', None)
    program_composite_key = eval(program_composite_key_str) if program_composite_key_str else None

    last_program_workout_instance_key_str = request.form.get('last_program_workout_instance_key', None)
    last_program_workout_instance_key = eval(last_program_workout_instance_key_str) if last_program_workout_instance_key_str else None

    adjustments_for_next_workout = request.form.get('adjustments_for_next_workout', None)

    workout_instance, exercises, program_entity, workout_instance_key, adjustments = _start_workout_logic(workout_key, 
                                                                                                          program_composite_key_str, 
                                                                                                          scheduled_workout_event_id,
                                                                                                          last_program_workout_instance_key,
                                                                                                          adjustments_for_next_workout)
  
    last = session.get(f"last_section_{workout_instance['id']}")  # no fallback
    
    # Get current workout state to see if there are any parameter overrides
    current_workout_state = get_active_workout_state()
    current_parameters = {}
    if current_workout_state:
        current_parameters = current_workout_state.get('exercise_parameters', {})
    if 'workout_sections' in workout_instance:
        workout_sections = workout_instance['workout_sections']
    else:
        workout_sections = workout_instance['sections']       
    return render_template(
        "workout_view.html",
        workout=workout_instance,
        workout_sections=workout_sections,
        exercises=exercises,
        current_parameters=current_parameters,
        default_section=last,
        program=program_entity,
        program_key=program_composite_key,
        workout_instance_key=workout_instance_key,
        scheduled_workout_event_id=scheduled_workout_event_id,
        finish_workout_url=url_for('program.finish_workout', workout_instance_key=workout_instance_key),
        cancel_workout_url=url_for('program.cancel_workout', workout_instance_key=workout_instance_key),
        adjustments=adjustments,
        show_finish_button=True,
        rs=rm_spaces
    )
 

@bp.route('/schedule_and_start', methods=['POST'])
@auth.login_required
def schedule_and_start(context=None):
    member = get_member_detail_from_user_context(context)
    mr = MembershipRegistry()
    short_name = mr.get_member(member.get('id', None)).get('short_name', member.get('id'))
    # This function is called when the user does not have a workout scheduled on their calendar
    # and they click on the "Start Workout" button
    # It will schedule the workout for now and then start it
    # It will also update the current state in the session
    # and return the workout view with the exercises

    # workout_key = eval(workout_instance_key) if workout_instance_key else None
    # es = EntityStore()
    # workout_instance = es.get_item_by_composite_key2(workout_key)
    
    # if not workout_instance:
    #     abort(404)

    # post to the google calendar service that the workout is finished

    program_key_str = request.form.get('program_key', None)
    workout_key_str = request.form.get('workout_key', None)

    last_program_workout_instance_key_str = request.form.get('last_program_workout_instance_key', None)
    last_program_workout_instance_key = eval(last_program_workout_instance_key_str) if last_program_workout_instance_key_str else None

    adjustments_for_next_workout = request.form.get('adjustments_for_next_workout', None)

    calendar_service = get_calendar_service()
    current_date = datetime.now().date().strftime("%Y-%m-%d")
    current_time = datetime.now().time().strftime("%H:%M")
    scheduled_workout_event_id = calendar_service.add_workout_event(member_short_name=member.get('short_name', short_name),
                                               event_date=current_date, event_time=current_time,
                                               location="YMCA", metadata=f'#id={member.get("id")}')
    
    workout_instance, exercises, program_entity, workout_instance_key, adjustments = _start_workout_logic(workout_key_str, 
                                                                                                          program_key_str, 
                                                                                                          scheduled_workout_event_id,
                                                                                                          last_program_workout_instance_key,
                                                                                                          adjustments_for_next_workout)
  
    last = session.get(f"last_section_{workout_instance['id']}")  # no fallback
    
    # Get current workout state to see if there are any parameter overrides
    current_workout_state = get_active_workout_state()
    current_parameters = {}
    if current_workout_state:
        current_parameters = current_workout_state.get('exercise_parameters', {})
    if 'workout_sections' in workout_instance:
        workout_sections = workout_instance['workout_sections']
    else:
        workout_sections = workout_instance['sections']       
    return render_template(
        "workout_view.html",
        workout=workout_instance,
        workout_sections=workout_sections,
        exercises=exercises,
        current_parameters=current_parameters,
        default_section=last,
        program=program_entity,
        program_key=program_key_str,
        workout_instance_key=workout_instance_key,
        scheduled_workout_event_id=scheduled_workout_event_id,
        finish_workout_url=url_for('program.finish_workout', workout_instance_key=workout_instance_key),
        cancel_workout_url=url_for('program.cancel_workout', workout_instance_key=workout_instance_key),
        adjustments=adjustments,
        show_finish_button=True,
        rs=rm_spaces
    )

def _start_workout_logic(workout_key, program_key, scheduled_workout_event_id, last_program_workout_instance_key, adjustments_for_next_workout_str):
    """
    Encapsulates the logic for starting a workout, including copying the workout,
    updating the program, and setting the session state.
    """
    es = EntityStore()
    workout_composite_key = eval(workout_key) if workout_key else None
    program_composite_key = eval(program_key) if program_key else None

    workout_entity = es.get_item_by_composite_key(workout_composite_key)
    program_entity = es.get_item_by_composite_key(program_composite_key)
    last_program_workout_instance = es.get_item_by_composite_key(last_program_workout_instance_key) if last_program_workout_instance_key else None
    adjustments_for_next_workout = eval(adjustments_for_next_workout_str) if adjustments_for_next_workout_str else {}   

    # we first copy the workout to the MemberWorkoutInstanceTable
    # all workouts in this program are bassed on the workout definitions in the MemberWorkoutDefinitionTable, that is the reps & sets for exercises are defined there
    # however, if there is a workout instance from a previous workout in the program, then we should copy the resistance & time parameters from that instance
    # to the new workout instance
    # then, finally, we will apply any adjustments that were made during the last workout to the new workout instance
    workout_instance = MemberWorkoutInstanceEntity(workout_entity.copy())
    if last_program_workout_instance:
        # go through each of the exercises in the last workout instance
        # and copy the parameters to the new workout instance
        for last_section, new_section in zip(last_program_workout_instance.get('workout_sections', []), workout_instance.get('workout_sections', [])):
            for last_exercise, new_exercise in zip(last_section.get('exercises', []), new_section.get('exercises', [])):
                # copy just the weight, units & time parameters from the last exercise to the new exercise
                last_params = last_exercise.get('parameters', {})
                new_params = new_exercise.get('parameters', {})
                new_params['weight'] = last_params.get('weight', 0)
                new_params['units'] = last_params.get('units', '')
                new_params['time'] = last_params.get('time', 0)
                new_exercise['parameters'] = new_params
    
    # now we want to apply the adjustments in the adjustments dict to the new workout instance
    # we do this by going through each of the  exercises in the workout instance
    # and applying the adjustments to the parameters of the exercises
    # for now, we will just apply the adjustment to the "weight" parameter, but we should figure out how to apply the adjustment to the time parameter as well
    # TODO:  figure out how to apply the adjustment to the time parameter as well
    if adjustments_for_next_workout:
        for section in workout_instance.get('workout_sections', []):
            for exercise in section.get('exercises', []):
                # apply the adjustments to the exercise parameters
                # check if the exercise has an adjustment in the adjustments_for_next_workout dict
                exercise_id = exercise.get('id', None)
                if exercise_id in adjustments_for_next_workout:
                    adjustment = adjustments_for_next_workout[exercise_id]
                    parameters = exercise.get('parameters', {})
                    current_weight_value = parameters.get('weight', 0)
                    if not current_weight_value:
                        current_weight_value = 0
                    adjusted_weight = int(current_weight_value) + adjustment
                    parameters['weight'] = adjusted_weight
                    # update the exercise parameters with the adjusted weight
                    exercise['parameters'] = parameters  

    workout_instance.update({
        'id': str(uuid.uuid4()),
        'started_ts': datetime.now().isoformat(),
        'finished_ts': "",
        'scheduled_workout_event_id': scheduled_workout_event_id,
        'member_workout_def_id': workout_entity['id'],
        'member_program_id': program_entity['id'],
        'member_program_name': program_entity.get('name', ''),
        'name': workout_entity.get('name', 'Unnamed Workout')
    })
    es.upsert_item(workout_instance)
    workout_instance_key = workout_instance.get_composite_key()

    # # add the workout instance to the program's workout_instances list
    # program_entity['workout_instances'] = program_entity.get('workout_instances', []) + [{'program_workout_instance_id': workout_instance.get('id'),
    #                                                                                       'program_workout_instance_key': workout_instance_key,
    #                                                                                       "started_ts": datetime.now().isoformat(),
    #                                                                                       "finished_ts": "",
    #                                                                                       "scheduled_workout_event_id": scheduled_workout_event_id}]
    # es.upsert_item(program_entity)

    wrkout_exercises = get_exercises_from_workout(workout_instance)
    exercises = {ex.get('id', None): ex for ex in wrkout_exercises}

    initialize_active_workout_state(workout_instance_key, program_key, scheduled_workout_event_id)
    adjustments = {}
    return workout_instance, exercises, program_entity, workout_instance_key, adjustments

   
@bp.route('/finish_workout/<workout_instance_key>', methods=['POST'])
@auth.login_required
def finish_workout(context=None, workout_instance_key=None):

    es = EntityStore()
    workout_composite_key = eval(workout_instance_key) if workout_instance_key else None
    workout_instance = es.get_item_by_composite_key(workout_composite_key)

    program_composite_key_str = request.form.get('program_key', None)
    program_composite_key = eval(program_composite_key_str) if program_composite_key_str else None
    program_entity = es.get_item_by_composite_key(program_composite_key)
    
    # post to the google calenard service that the workout is finished
    scheduled_workout_event_id = request.form.get('scheduled_workout_event_id', None)

    current_workout_state = get_active_workout_state()
    adjustments_for_next_workout = current_workout_state.get('adjustments', {})
    exercise_parameters = current_workout_state.get('exercise_parameters', {})

    # here we want to update the parameters of the exercises in the workout instance
    # with the parameters from the current workout state
    # clear the 'current_workout_instance_state' from the session
    for exercise, params in exercise_parameters.items():
        for section in workout_instance.get('workout_sections', []):
            for ex in section.get('exercises', []):
                if ex.get('id', None) == exercise:
                    ex['parameters'] = params
    
    workout_instance['finished_ts'] = datetime.now().isoformat()
    workout_instance['adjustments_for_next_workout'] = adjustments_for_next_workout
    
    es.upsert_item(workout_instance)
    
    clear_active_workout_state()
    # session.pop('current_workout_instance_state', None)
    session.pop(f"last_section_{workout_instance['id']}", None)


    cal = get_calendar_service()
    cal.update_status_of_workout_event(scheduled_workout_event_id, 'done')

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


    # clear the 'current_workout_instance_state' from the session
    clear_active_workout_state()
    # session.pop('current_workout_instance_state', None)
    session.pop(f"last_section_{workout_instance['id']}", None)

    # remove the workout_instance from the entity store
    es.delete_item(workout_instance)

    return redirect('/', 302)

