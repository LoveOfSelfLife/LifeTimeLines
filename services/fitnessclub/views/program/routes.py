from datetime import datetime
import json
import uuid
from flask import Blueprint, abort, current_app, make_response, redirect, render_template, request, url_for
from common.entity_store import EntityStore
from common.fitness.active_fitness_registry import get_fitnessclub_entity_filters_for_entity, get_fitnessclub_entity_type_for_entity, get_fitnessclub_filter_func_for_entity, get_fitnessclub_filter_term_func_for_entity, get_fitnessclub_listing_fields_for_entity
from common.fitness.entities_getter import get_entity, get_entity2, get_filtered_entities
from common.fitness.hx_common import hx_render_template
from common.fitness.member_entity import MembershipRegistry, get_member_detail_from_user_context
from common.fitness.program_entity import ProgramEntity
from common.fitness.workout_entity import ProgramWorkoutEntity
bp = Blueprint('program', __name__, template_folder='templates')
from auth import auth

@bp.route('/')
@auth.login_required
def index(context=None):
    return redirect(url_for('program.programs_listing'), 302)

@bp.route('/programs-listing')
@auth.login_required
def programs_listing(context=None):
    member = get_member_detail_from_user_context(context)
    PROGRAM_ENTITY_NAME = "ProgramTable"
    page = int(request.args.get('page', 1))
    page_size = 10
    view = request.args.get('view', 'list')
    fields_to_display  = get_fitnessclub_listing_fields_for_entity(PROGRAM_ENTITY_NAME)
    filters = get_fitnessclub_entity_filters_for_entity(PROGRAM_ENTITY_NAME)

    if filters:
        filter_func  = get_fitnessclub_filter_func_for_entity(PROGRAM_ENTITY_NAME)
        filter_term_func  = get_fitnessclub_filter_term_func_for_entity(PROGRAM_ENTITY_NAME)
        filter_terms = filter_term_func(request.args)
    else:
        filter_func = None
        filter_terms = None

    entities = get_filtered_entities(PROGRAM_ENTITY_NAME, fields_to_display, filter_func, filter_terms, partition_key=member.get('id', None))

    total_pages = (len(entities) + page_size - 1) // page_size
    start = (page - 1) * page_size
    end = start + page_size
    current = entities[start:end]

    # displays workouts at the top level
    return hx_render_template(
        "entity_list_component.html",
        entity_name=PROGRAM_ENTITY_NAME,
        main_content_container="entities-container",        
        fields_to_display=fields_to_display,
        entities=current,
        filter_terms=filter_terms,
        args=request.args,
        page=page,
        view=view,
        entity_add_route=url_for('program.builder_new'),        
        total_pages=total_pages,
        entity_view_route=f'/program/viewer?entity_table={PROGRAM_ENTITY_NAME}',
        entities_listing_route=f'/program/programs-listing?entity_table={PROGRAM_ENTITY_NAME}',
        entity_action_route=f'/program/edit?entity_table={PROGRAM_ENTITY_NAME}',
        entity_action_icon='bi-pencil-square',  
        entity_action_label='Edit Program',       
        context=context)

@bp.route('/viewer')
@auth.login_required
def program_viewer(context=None):
    return hx_render_template(
        "program_viewer.html",
        entity_name="ProgramTable",
        main_content_container="entities-container",
        fields_to_display=['name', 'description', 'start_date', 'end_date', 'workouts'],
        args=request.args,
        context=context
    )    

@bp.route('/workouts-listing')
@auth.login_required
def workouts_listing(context=None):
    WORKOUT_ENTITY_NAME = "WorkoutTable"
    program_id = request.args.get('program_id')
    page = int(request.args.get('page', 1))
    view = request.args.get('view', 'list')
    page_size = 10
    target = request.args.get('target')
    fields_to_display  = get_fitnessclub_listing_fields_for_entity(WORKOUT_ENTITY_NAME)
    filters = get_fitnessclub_entity_filters_for_entity(WORKOUT_ENTITY_NAME)

    redis_client = current_app.config['SESSION_CACHELIB']
    current_program = redis_client.get('current_program')
    mobile = request.args.get('mobile', type=bool, default=False)
    div_id = 'lib-list-mobile' if mobile else 'lib-list'
    target = div_id

    if current_program:
        p = json.loads(current_program)
        if p['id'] != program_id:
            abort(404)
    else:
            abort(404)     

    if filters:
        filter_func  = get_fitnessclub_filter_func_for_entity(WORKOUT_ENTITY_NAME)
        filter_term_func  = get_fitnessclub_filter_term_func_for_entity(WORKOUT_ENTITY_NAME)
        filter_terms = filter_term_func(request.args)
    else:
        filter_func = None
        filter_terms = None

    entities = get_filtered_entities(WORKOUT_ENTITY_NAME, fields_to_display, filter_func, filter_terms)

    total_pages = (len(entities) + page_size - 1) // page_size
    start = (page - 1) * page_size
    end = start + page_size
    current = entities[start:end]

    # displays workouts at the top level
    return hx_render_template(
        "entity_list_component.html",
        fields_to_display=fields_to_display,
        main_content_container=div_id,        
        entities=current,
        entity_name=WORKOUT_ENTITY_NAME,

        filter_terms=filter_terms,
        args=request.args,
        page=page,
        view=view,
        total_pages=total_pages,
        entities_listing_route=f'/program/workouts-listing?entity_table={WORKOUT_ENTITY_NAME}&target={target}&program_id={program_id}',
        entity_view_route=f'/workouts/viewer/workout?entity_table={WORKOUT_ENTITY_NAME}',
        entity_action_route=f'/program/builder/{program_id}/add?entity_table={WORKOUT_ENTITY_NAME}',
        entity_action_route_method='post',
        entity_action_route_target="program-canvas",
        entity_action_icon='bi-plus',  
        entity_action_label='Add Workout',       
        context=context)

def new_program(name='New workout program', member_id=None):
    program_id = str(uuid.uuid4())
    return {
        'id': program_id,
        'member_id': member_id,
        'name': name,
        'start_date': None,
        'end_date': None,
        'workouts': []
    }
@bp.route('/edit')
@auth.login_required
def edit_program_details(context=None):
    PROGRAM_ENTITY_NAME = "ProgramTable"
    entity_instance = get_fitnessclub_entity_type_for_entity(PROGRAM_ENTITY_NAME)

    composite_key_str = request.args.get('key', None)
    composite_key = eval(composite_key_str) if composite_key_str else None
    es = EntityStore()
    entity_to_view = es.get_item_by_composite_key2(composite_key)
    entity_type = get_fitnessclub_entity_type_for_entity(PROGRAM_ENTITY_NAME)
    entity_type.initialize(entity_to_view)
    print(f"editing program: {json.dumps(entity_to_view, indent=4)}")
    redis_client = current_app.config['SESSION_CACHELIB']
    redis_client.set('current_program', json.dumps(entity_type))

    return redirect(url_for('program.builder', program_id=entity_type['id']))


@bp.route('/builder/new')
@auth.login_required
def builder_new(context=None):
    member = get_member_detail_from_user_context(context)
    p = new_program(member_id=member['id'])

    redis_client = current_app.config['SESSION_CACHELIB']
    redis_client.set('current_program', json.dumps(p))

    return redirect(url_for('program.builder', program_id=p['id']))

# ── Main Builder View ─────────────────────────────────────────────
@bp.route('/builder/<program_id>')
@auth.login_required
def builder(context=None, program_id=None):
    member = get_member_detail_from_user_context(context)

    PROGRAM_ENTITY_NAME = "ProgramTable"
    redis_client = current_app.config['SESSION_CACHELIB']
    current_program = redis_client.get('current_program')
    if current_program:
        program = json.loads(current_program)
        if program['id'] == program_id:
            return hx_render_template('program_builder.html', program=program, context=context)
    abort(404)

@bp.route('/builder/<program_id>/reorder', methods=['POST'])
@auth.login_required
def reorder_workouts(context=None, program_id=None):
    # retrieve the workut from redis
    redis_client = current_app.config['SESSION_CACHELIB']
    current_program = redis_client.get('current_program')
    p = json.loads(current_program)

    order = request.form.getlist('order[]')
    lookup = {it['id']:it for it in p['workouts']}
    p['workouts'] = [lookup[i] for i in order if i in lookup]

    # here we save the program to redis
    redis_client.set('current_program', json.dumps(p))
    
    return program_canvas2(context, program_id)

@bp.route('/builder/<program_id>/updatename', methods=['POST'])
@auth.login_required
def update_program_name(context=None, program_id=None):

    # retrieve the workut from redis
    redis_client = current_app.config['SESSION_CACHELIB']
    current_program = redis_client.get('current_program')
    p = json.loads(current_program)
    
    p['name'] = request.form['name']

    # here we save the workout to redis
    redis_client.set('current_program', json.dumps(p))
    return program_canvas2(context, program_id)

def program_canvas2(context=None, program_id=None):
    redis_client = current_app.config['SESSION_CACHELIB']
    current_program = redis_client.get('current_program')
    if current_program:
        p = json.loads(current_program)

        program_workouts = get_workouts_from_program(p)
        workouts = { wk.get('id', None): wk for wk in program_workouts }
        # workouts = p['workouts'] if 'workouts' in p else []
        # workouts = { wk.get('id', None): wk for wk in p['workouts'] if 'id' in wk}
        if p['id'] == program_id:
            return hx_render_template('_program_canvas.html',
                                        program=p,
                                        workouts=workouts,
                                        context=context)
    abort(404)

def get_workouts_from_program(program):
    workouts = []
    es = EntityStore()
    for w in program['workouts']:
        e = es.get_item_by_composite_key2(w['key'])
        # ek = get_entity2(ProgramWorkoutEntity(), w['id'], partition_key=program['id'])
        workouts.append(e)
    return workouts

@bp.route('/builder/<program_id>/save', methods=['POST'])
@auth.login_required
def save_program(context=None, program_id=None):
    member_id = get_member_detail_from_user_context(context).get('id', None)
    if not member_id:
        abort(401)    

    PROGRAM_ENTITY_NAME = "ProgramTable"
    redis_client = current_app.config['SESSION_CACHELIB']
    current_program = redis_client.get('current_program')
    if current_program:
        program = json.loads(current_program)
        if program['id'] != program_id:
            abort(404)

    # the workouts in the program.workouts list are from teh WorkoutTable
    # we will copy thos workout objects into the ProgramWorkoutTable, then use the id & Program_id of that copy to populate the program.workouts list

    # create a new program instance
    program_instance : ProgramEntity = get_fitnessclub_entity_type_for_entity(PROGRAM_ENTITY_NAME)
    program_instance.initialize(program)    
    program_instance['created_ts'] = datetime.now().isoformat()
    es = EntityStore()
    workouts_in_program = []
    for wk in program['workouts']:
        wk_id = wk['id']
        # get the workout entity
        # wk_entity = get_entity("WorkoutTable", wk_id)
        wk_entity = es.get_item_by_composite_key2(wk['key'])
        if not wk_entity:
            abort(404)
        wk_entity['id'] = str(uuid.uuid4())  # generate a new id for the program workout
        wk_entity['program_id'] = program['id']  # set the program id for the workout
        wk_entity['parent_workout_id'] = wk_id  # keep the original workout id for reference
        workout_copy = ProgramWorkoutEntity(wk_entity)
        workouts_in_program.append(workout_copy)
        
    # add the IDs of the newly copied workouts to the new program's workouts list
    program_instance['workouts'] = [{'id': workout_copy['id'], 'program_id': program['id'], 'key' : workout_copy.get_composite_key()} for workout_copy in workouts_in_program]


    es = EntityStore()

    # this is where we save the newly created progrm
    # first save the program workouts to the ProgramWorkoutTable
    print('Saving program')
    es.upsert_items(workouts_in_program)
    es.upsert_item(program_instance)
    # remove from redis
    redis_client.delete('current_program')

    response = make_response('')
    response.headers['HX-Trigger'] = json.dumps({
        "eventListChanged": True,
        "showMessage": f"saved program"
    })

    return redirect(url_for('program.index'), 302, response)

@bp.route('/builder/<program_id>/remove', methods=['POST'])
@auth.login_required
def remove_workout(context=None, program_id=None):

    # retrieve the workut from redis
    redis_client = current_app.config['SESSION_CACHELIB']
    current_program = redis_client.get('current_program')
    p = json.loads(current_program)

    wk_id = request.form['workout_id']
    
    p['workouts'] = [it for it in p['workouts'] if it['id']!=wk_id]

    # here we save the workout to redis
    redis_client.set('current_program', json.dumps(p))
    return program_canvas2(context, program_id)

@bp.route('/builder/<program_id>/canvas')
@auth.login_required
def program_canvas(context=None, program_id=None):
    return program_canvas2(context, program_id)

@bp.route('/builder/<program_id>/add', methods=['POST'])
@auth.login_required
def add_workout(context=None, program_id=None):

    # retrieve the workut from redis
    redis_client = current_app.config['SESSION_CACHELIB']
    current_program = redis_client.get('current_program')
    if current_program:
        p = json.loads(current_program)
        if p['id'] != program_id:
            abort(404)

    # here we get the key of the workout from the query parameters
    # and we look it up in the workouts table
    # if it is not found we abort with a 404
    # if it is found we add it to the workout
    # and we save the workout to redis
    composite_key_str = request.args.get('key', None)
    composite_key = eval(composite_key_str) if composite_key_str else None
    es = EntityStore()
    entity_instance = get_fitnessclub_entity_type_for_entity("WorkoutTable")
    wk = es.get_item_by_composite_key2(composite_key)
    if not wk:
        abort(404)
    
    # wk_id = wk['id']

    if wk['id'] not in p['workouts']:
        # add the workout to the program
        p['workouts'].append({'key': wk.get_composite_key(), 'id':wk['id'], "name": wk['name']})


    # here we save the program to redis
    redis_client.set('current_program', json.dumps(p))

    return program_canvas2(context, program_id)

