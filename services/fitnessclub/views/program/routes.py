from datetime import datetime
import json
import uuid
from flask import Blueprint, abort, current_app, make_response, redirect, render_template, request, session, url_for
from common.entity_store import EntityStore
from common.fitness.active_fitness_registry import get_fitnessclub_entity_filters_for_entity, get_fitnessclub_entity_type_for_entity, get_fitnessclub_filter_func_for_entity, get_fitnessclub_filter_term_func_for_entity, get_fitnessclub_listing_fields_for_entity
from common.fitness.cacher import delete_from_cache, get_cache_value, set_cache_value
from common.fitness.entities_getter import get_entity, get_entity2, get_filtered_entities
from common.fitness.get_calendar_service import get_calendar_service
from common.fitness.hx_common import hx_render_template
from common.fitness.member_entity import MembershipRegistry, get_member_detail_from_user_context
from common.fitness.program_entity import ProgramEntity
from common.fitness.workout_entity import ProgramWorkoutEntity, ProgramWorkoutInstanceEntity, get_exercises_from_workout
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

    view = request.args.get('view', None)
    if view:
        session['view_preference'] = view
    else:
        view = session.get('view_preference', 'list')

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

    view = request.args.get('view', None)
    if view:
        session['view_preference'] = view
    else:
        view = session.get('view_preference', 'list')

    page_size = 10
    target = request.args.get('target')
    fields_to_display  = get_fitnessclub_listing_fields_for_entity(WORKOUT_ENTITY_NAME)
    filters = get_fitnessclub_entity_filters_for_entity(WORKOUT_ENTITY_NAME)
    mobile = request.args.get('mobile', type=bool, default=False)
    div_id = 'lib-list-mobile' if mobile else 'lib-list'
    target = div_id
    current_program = get_cache_value('current_program')

    if current_program:
        if current_program['id'] != program_id:
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

@bp.route('/builder/new')
@auth.login_required
def builder_new(context=None):
    member = get_member_detail_from_user_context(context)
    p = new_program(member_id=member['id'])

    set_cache_value('current_program', p)
    delete_from_cache('current_program_workouts')
    return redirect(url_for('program.builder'))

@bp.route('/edit')
@auth.login_required
def edit_program_details(context=None):
    es = EntityStore()

    composite_key_str = request.args.get('key', None)
    composite_key = eval(composite_key_str) if composite_key_str else None
    program = ProgramEntity(es.get_item_by_composite_key2(composite_key))
    
    set_cache_value('current_program', program)
    delete_from_cache('current_program_workouts')
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
            workouts = { wk.get('id', None): wk for wk in program_workouts }
            for wk in workouts.values():
                wk['key'] = wk.get_composite_key()
                wk['key_str'] = '|'.join(wk.get_composite_key())
            # store the workouts in the cache as well
            set_cache_value('current_program_workouts', workouts)
        else:
            workouts = get_cache_value('current_program_workouts')

        if p['id'] == program_id:
            return hx_render_template('_program_canvas2.html',
                                        program=p,
                                        workouts=workouts,
                                        context=context)
    abort(404)


@bp.route("/viewer/workout2/<workout_id>")
@auth.login_required
def view_workout2(context=None, workout_id=None):
    member_id = get_member_detail_from_user_context(context).get('id', None)

    current_program = get_cache_value('current_program')
    current_program_workouts = get_cache_value('current_program_workouts')
    
    workout = current_program_workouts.get(workout_id, None)

    # workout_key_pipe_delimited_str = request.args.get('keyStrPipeDelimited', None)
    # # Convert pipe-delimited string to a list
    # workout_composite_key = workout_key_pipe_delimited_str.split('|')
    # workout = EntityStore().get_item_by_composite_key2(workout_composite_key)
    # if not workout:
    #     abort(404)
    
    program_id = request.args.get('program_id', None)

    wrkout_exercises = get_exercises_from_workout(workout)
    exercises = { ex.get('id', None): ex for ex in wrkout_exercises }

    return render_template(
        "workout_view2.html",
        program=None,  # No program context in this view
        workout=workout,
        exercises=exercises,
        program_id=program_id,
        member_id=member_id
    )

@bp.route('/builder/<workout_id>/update_param', methods=['POST'])
@auth.login_required
def update_param(context=None, workout_id=None):

    workouts = get_cache_value('current_program_workouts')
    current_workout = workouts.get(workout_id, None)
    if not current_workout:
        abort(404)

    exid  = request.form['exercise_id']

    program_id = request.form.get('program_id', None)
    param = request.form['param']
    value = request.form['value'] or None
    for s in current_workout['sections']:
        for it in s['exercises']:
            if it['id']==exid:
                it['parameters'][param] = value

    workouts[workout_id] = current_workout
    set_cache_value('current_program_workouts', workouts)

    return ('', 204)


@bp.route('/builder/<program_id>/reorder', methods=['POST'])
@auth.login_required
def reorder_workouts(context=None, program_id=None):

    p = get_cache_value('current_program')

    order = request.form.getlist('order[]')
    lookup = {it['id']:it for it in p['workouts']}
    p['workouts'] = [lookup[i] for i in order if i in lookup]

    # here we save the program to the cache
    set_cache_value('current_program', p)
    
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

def get_workouts_from_program(program):
    workouts = []
    es = EntityStore()
    for w in program['workouts']:
        e = es.get_item_by_composite_key2(w['key'])
        workouts.append(e)
    return workouts

@bp.route('/builder/<program_id>/save', methods=['POST'])
@auth.login_required
def save_program(context=None, program_id=None):
    member_id = get_member_detail_from_user_context(context).get('id', None)
    if not member_id:
        abort(401)    

    PROGRAM_ENTITY_NAME = "ProgramTable"
    current_program = get_cache_value('current_program')
    if current_program:
        if current_program['id'] != program_id:
            abort(404)

    # # create a new program instance
    # program_instance = ProgramEntity(current_program)  # create a new instance of ProgramEntity with the current program data
    # program_instance['id'] = str(uuid.uuid4())  # generate a new id for the program
    # program_instance['created_ts'] = datetime.now().isoformat()
        
    # # add the IDs of the newly copied workouts to the new program's workouts list
    # program_instance['workouts'] = [{'id': workout_copy['id'], 
    #                                  'program_id': current_program['id'], 
    #                                  'key' : workout_copy.get_composite_key()} for workout_copy in workouts_in_program]

    es = EntityStore()

    workouts_in_program = []
    current_program_workouts = get_cache_value('current_program_workouts')
    for p in current_program_workouts.values():
        workouts_in_program.append(ProgramWorkoutEntity(p))

    es.upsert_items(workouts_in_program)
    es.upsert_item(ProgramEntity(current_program))

    delete_from_cache('current_program')
    delete_from_cache('current_program_workouts')

    response = make_response('')
    response.headers['HX-Trigger'] = json.dumps({
        "eventListChanged": True,
        "showMessage": { "value" : f"saved program", "target": "body" }
    })

    return redirect(url_for('program.index'), 302, response)

@bp.route('/builder/<program_id>/remove', methods=['POST'])
@auth.login_required
def remove_workout(context=None, program_id=None):

    p = get_cache_value('current_program')

    wk_id = request.form['workout_id']
    
    p['workouts'] = [it for it in p['workouts'] if it['id']!=wk_id]

    set_cache_value('current_program', p)
    return program_canvas2(context, program_id)


@bp.route('/builder/<program_id>/add', methods=['POST'])
@auth.login_required
def add_workout(context=None, program_id=None):

    current_program = get_cache_value('current_program')
    current_program_workouts = get_cache_value('current_program_workouts')
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

    added_workout = EntityStore().get_item_by_composite_key2(composite_key)
    if not added_workout:
        abort(404)

    added_workout_id = added_workout['id']
    added_workout['id'] = str(uuid.uuid4())  # generate a new id for the program workout
    added_workout['program_id'] = current_program['id']  # set the program id for the workout
    added_workout['parent_workout_id'] = added_workout_id  # keep the original workout id for reference
    workout_copy = ProgramWorkoutEntity(added_workout)

    workout_copy['key'] = workout_copy.get_composite_key()
    workout_copy['key_str'] = '|'.join(workout_copy.get_composite_key())    

    current_program['workouts'].append({'key': workout_copy.get_composite_key(), 'id':workout_copy['id'], "name": workout_copy['name']})
    current_program_workouts[workout_copy['id']] = workout_copy

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

    workout_instance, exercises, program_entity, workout_instance_key = _start_workout_logic(workout_key, program_composite_key_str, scheduled_workout_event_id)

  
    last = session.get(f"last_section_{workout_instance['id']}")  # no fallback

    return render_template(
        "workout_view.html",
        workout=workout_instance,
        exercises=exercises,
        default_section=last,
        program=program_entity,
        program_key=program_composite_key,
        workout_instance_key=workout_instance_key,
        scheduled_workout_event_id=scheduled_workout_event_id,
        finish_workout_url=url_for('program.finish_workout', workout_instance_key=workout_instance_key),
        show_finish_button=True
    )
 
@bp.route('/finish_workout/<workout_instance_key>', methods=['POST'])
@auth.login_required
def finish_workout(context=None, workout_instance_key=None):

    es = EntityStore()
    workout_composite_key = eval(workout_instance_key) if workout_instance_key else None
    workout_instance = es.get_item_by_composite_key2(workout_composite_key)

    program_composite_key_str = request.form.get('program_key', None)
    program_composite_key = eval(program_composite_key_str) if program_composite_key_str else None
    program_entity = es.get_item_by_composite_key2(program_composite_key)
    
    # post to the google calenard service that the workout is finished
    scheduled_workout_event_id = request.form.get('scheduled_workout_event_id', None)

    # clear the 'current_workout_instance_state' from the session
    session.pop('current_workout_instance_state', None)
    session.pop(f"last_section_{workout_instance['id']}", None)

    workout_entity = es.get_item_by_composite_key2(workout_composite_key)    
    program_entity = es.get_item_by_composite_key2(program_composite_key)    

    list_of_workout_instances = program_entity.get('workout_instances', [])
    # find the workout instance in the program's workout_instances list
    for instance in list_of_workout_instances:
        if instance.get('program_workout_instance_id') == workout_instance['id']:
            # update the finished timestamp for the workout instance
            instance['finished_ts'] = datetime.now().isoformat()
            # update the workout instance in the program's workout_instances list
            program_entity['workout_instances'] = list_of_workout_instances
            es.upsert_item(program_entity)    
            break
    else:
        # if we didn't find the workout instance, we can log an error or raise an exception
        current_app.logger.error(f"Workout instance {workout_instance_key} not found in program {program_composite_key}")
        abort(404)
    cal = get_calendar_service()
    cal.update_status_of_workout_event(scheduled_workout_event_id, 'done')

    return redirect('/')

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

    calendar_service = get_calendar_service()
    current_date = datetime.now().date().strftime("%Y-%m-%d")
    current_time = datetime.now().time().strftime("%H:%M")
    scheduled_workout_event_id = calendar_service.add_workout_event(member_short_name=member.get('short_name', short_name),
                                               event_date=current_date, event_time=current_time,
                                               location="YMCA", metadata=f'#id={member.get("id")}')
    
    workout_instance, exercises, program_entity, workout_instance_key = _start_workout_logic(workout_key_str, program_key_str, scheduled_workout_event_id)
  
    last = session.get(f"last_section_{workout_instance['id']}")  # no fallback

    return render_template(
        "workout_view.html",
        workout=workout_instance,
        exercises=exercises,
        default_section=last,
        program=program_entity,
        program_key=program_key_str,
        workout_instance_key=workout_instance_key,
        scheduled_workout_event_id=scheduled_workout_event_id,
        finish_workout_url=url_for('program.finish_workout', workout_instance_key=workout_instance_key),
        show_finish_button=True
    )

def _start_workout_logic(workout_key, program_key, scheduled_workout_event_id):
    """
    Encapsulates the logic for starting a workout, including copying the workout,
    updating the program, and setting the session state.
    """
    es = EntityStore()
    workout_composite_key = eval(workout_key) if workout_key else None
    program_composite_key = eval(program_key) if program_key else None

    workout_entity = es.get_item_by_composite_key2(workout_composite_key)
    program_entity = es.get_item_by_composite_key2(program_composite_key)

    # copy the workout to the ProgramWorkoutInstanceTable
    # then get the ID of the newly created workout instance and populate it into the program's workout_instances list
    workout_instance = ProgramWorkoutInstanceEntity(workout_entity.copy())
    workout_instance.update({
        'id': str(uuid.uuid4()),
        'program_workout_id': workout_entity['id']
    })
    es.upsert_item(workout_instance)
    workout_instance_key = workout_instance.get_composite_key()

    # add the workout instance to the program's workout_instances list
    program_entity['workout_instances'] = program_entity.get('workout_instances', []) + [{'program_workout_instance_id': workout_instance.get('id'),
                                                                                          'program_workout_instance_key': workout_instance_key,
                                                                                          "started_ts": datetime.now().isoformat(),
                                                                                          "finished_ts": "",
                                                                                          "scheduled_workout_event_id": scheduled_workout_event_id}]
    es.upsert_item(program_entity)

    wrkout_exercises = get_exercises_from_workout(workout_instance)
    exercises = {ex.get('id', None): ex for ex in wrkout_exercises}

    current_state = {
        'state': 'workout_started',
        'workout_instance_key': workout_instance_key,
        'program_key': program_composite_key,
        'scheduled_workout_event_id': scheduled_workout_event_id
    }
    current_state_str = json.dumps(current_state)
    session['current_workout_instance_state'] = current_state_str

    return workout_instance, exercises, program_entity, workout_instance_key
     