from datetime import datetime
from flask import Blueprint, jsonify, make_response, render_template, request, current_app
from common.entity_store import EntityStore
from common.fitness.active_fitness_registry import get_fitnessclub_entity_filters_for_entity, get_fitnessclub_entity_type_for_entity, get_fitnessclub_filter_func_for_entity, get_fitnessclub_filter_term_func_for_entity, get_fitnessclub_listing_fields_for_entity
from common.fitness.cacher import get_cache_value, set_cache_value, delete_from_cache
from common.fitness.entities_getter import get_filtered_entities
from common.fitness.exercise_entity import ExerciseEntity
from common.fitness.hx_common import hx_render_template
from common.fitness.workout_entity import get_exercises_from_workout
bp = Blueprint('workouts', __name__, template_folder='templates')
from auth import auth
from flask import Flask, render_template, request, redirect, url_for, session, abort
import uuid
import json
from common.fitness.workout_entity import WorkoutEntity
from common.fitness.exercise_entity import ExerciseEntity, ExerciseReviewEntity

from common.fitness.entities_getter import get_filtered_entities, get_entity


def new_workout(name='New Workout'):
    wid = str(uuid.uuid4())
    return {
        'id': wid,
        'name': name,
        'sections': [
            {'name':'warmup','exercises':[]},
            {'name':'core','exercises':[]},
            {'name':'combination','exercises':[]},
            {'name':'strength','exercises':[]},
            {'name':'cardio','exercises':[]},
        ]
    }

# ──────────────────────────────────────────────────

@bp.route('/')
@auth.login_required
def index(context=None):
    return redirect(url_for('workouts.workouts_listing'), 302)

@bp.route('/workouts-listing')
@auth.login_required
def workouts_listing(context=None):
    WORKOUT_ENTITY_NAME = "WorkoutTable"
    page = int(request.args.get('page', 1))
    # view = request.args.get('view', 'list')
    target = request.args.get('target', None)    

    view = request.args.get('view', None)
    if view:
        session['view_preference'] = view
    else:
        view = session.get('view_preference', 'list')

    fields_to_display  = get_fitnessclub_listing_fields_for_entity(WORKOUT_ENTITY_NAME)
    filters = get_fitnessclub_entity_filters_for_entity(WORKOUT_ENTITY_NAME)

    if filters:
        filter_func  = get_fitnessclub_filter_func_for_entity(WORKOUT_ENTITY_NAME)
        filter_term_func  = get_fitnessclub_filter_term_func_for_entity(WORKOUT_ENTITY_NAME)
        filter_terms = filter_term_func(request.args)
    else:
        filter_func = None
        filter_terms = None

    entities = get_filtered_entities(WORKOUT_ENTITY_NAME, fields_to_display, filter_func, filter_terms)

    page_size = 10
    total_pages = (len(entities) + page_size - 1) // page_size
    start = (page - 1) * page_size
    end = start + page_size
    current = entities[start:end]

    # displays workouts at the top level
    return render_template(
        "entity_list_component.html",
        entity_name=WORKOUT_ENTITY_NAME,
        main_content_container="entities-container",        
        fields_to_display=fields_to_display,
        entities=current,
        filter_terms=filter_terms,
        args=request.args,
        page=page,
        view=view,
        total_pages=total_pages,
        entity_add_route=url_for('workouts.builder_new'),
        entities_listing_route=f'/workouts/workouts-listing?entity_table={WORKOUT_ENTITY_NAME}&target={target}',
        entity_view_route=f'/workouts/viewer/workout?entity_table={WORKOUT_ENTITY_NAME}',
        entity_action_route=f'/workouts/edit?entity_table={WORKOUT_ENTITY_NAME}',
        entity_action_icon='bi-pencil-square',  
        entity_action_label='Edit Workout',       
        # filter_dialog_route=f'/exercises/filter-dialog?entity_table={WORKOUT_ENTITY_NAME}',
        context=context)

@bp.route('/filter-dialog')
@auth.login_required
def filter_dialog(context=None):
    target = request.args.get('target', None)
    workout_id = request.args.get('workout_id', None)
    entity_name = "ExerciseTable"
    entity_type = get_fitnessclub_entity_type_for_entity(entity_name)
    filters = get_fitnessclub_entity_filters_for_entity(entity_name)

    return hx_render_template('filter_dialog.html', 
                              entities_listing_route=f'/workouts/builder/exercises?entity_table={entity_name}&target={target}&workout_id={workout_id}',
                              filter_results_target=target,
                              entity_display_name=entity_type.get_display_name(),                              
                              entity_name=entity_name,
                              filters=filters,
                              args=request.args,
                              context=context)

@bp.route('/view')
@auth.login_required
def view_workout_details(context=None):
    # table_id = "WorkoutTable"
    # entity_instance = get_fitnessclub_entity_type_for_entity(table_id)

    # composite_key_str = request.args.get('key', None)
    # composite_key = eval(composite_key_str) if composite_key_str else None
    # es = EntityStore()
    # entity_to_view = es.get_item_by_composite_key(entity_instance, composite_key)
    
    # return render_workout_popup_viewer_html(context, entity_to_view)
    WORKOUT_ENTITY_NAME = "WorkoutTable"
    entity_instance = get_fitnessclub_entity_type_for_entity(WORKOUT_ENTITY_NAME)

    composite_key_str = request.args.get('key', None)
    composite_key = eval(composite_key_str) if composite_key_str else None
    es = EntityStore()
    entity_to_view = es.get_item_by_composite_key2(composite_key)
    entity_type = get_fitnessclub_entity_type_for_entity(WORKOUT_ENTITY_NAME)
    entity_type.initialize(entity_to_view)

    set_cache_value('current_workout', entity_type)
    return redirect(url_for('workouts.builder', workout_id=entity_type['id']))

@bp.route('/edit')
@auth.login_required
def edit_workout_details(context=None):
    WORKOUT_ENTITY_NAME = "WorkoutTable"
    entity_instance = get_fitnessclub_entity_type_for_entity(WORKOUT_ENTITY_NAME)

    composite_key_str = request.args.get('key', None)
    composite_key = eval(composite_key_str) if composite_key_str else None
    es = EntityStore()
    entity_to_view = es.get_item_by_composite_key2(composite_key)
    entity_type = get_fitnessclub_entity_type_for_entity(WORKOUT_ENTITY_NAME)
    entity_type.initialize(entity_to_view)
    print(f"editing workoug: {json.dumps(entity_to_view, indent=4)}")
    set_cache_value('current_workout', entity_type)
    
    return redirect(url_for('workouts.builder', workout_id=entity_type['id']))


@bp.route('/builder/new')
@auth.login_required
def builder_new(context=None):
    w = new_workout()
    set_cache_value('current_workout', w)

    return redirect(url_for('workouts.builder', workout_id=w['id']))

# ── Main Builder View ─────────────────────────────────────────────
@bp.route('/builder/<workout_id>')
@auth.login_required
def builder(context=None, workout_id=None):
    WORKOUT_ENTITY_NAME = "WorkoutTable"
    workout = get_cache_value('current_workout')
    if workout and workout['id'] == workout_id:
            return hx_render_template('builder.html', workout=workout, context=context, source='exercises')

    entity_type = get_fitnessclub_entity_type_for_entity(WORKOUT_ENTITY_NAME)
    entity_type['id'] = workout_id
    es = EntityStore()
    workout = es.get_item(entity_type)
    if not workout:
        abort(404)

    set_cache_value('current_workout', workout)
    return hx_render_template('builder.html', workout=workout, context=context, source='exercises')

# ── Fragments ────────────────────────────────────────────────────

    
@bp.route('/builder/<workout_id>/canvas')
@auth.login_required
def workout_canvas(context=None, workout_id=None):
    return workout_canvas2(context, workout_id)

def workout_canvas2(context=None, workout_id=None):
    w =  get_cache_value('current_workout')
    if w:
        wrkout_exercises = get_exercises_from_workout(w)
        exercises = { ex.get('id', None): ex for ex in wrkout_exercises }

        if w['id'] == workout_id:
            return hx_render_template('_workout_canvas.html',
                                        workout=w,
                                        exercises=exercises, context=context)
    abort(404)

# ── Actions ──────────────────────────────────────────────────────

@bp.route('/builder/<workout_id>/add', methods=['POST'])
@auth.login_required
def add_exercise(context=None, workout_id=None):

    w = get_cache_value('current_workout')
    if w:
        if w['id'] != workout_id:
            abort(404)
    else:
        # if there is no workout in the cache, we create a new one
        w = new_workout()
        set_cache_value('current_workout', w)

    # here we get the key of the exercise from the query parameters
    # and we look it up in the exercise catalog
    # if it is not found we abort with a 404
    # if it is found we add it to the workout
    # and we save the workout to the redis cache
    composite_key_str = request.args.get('key', None)
    composite_key = eval(composite_key_str) if composite_key_str else None
    es = EntityStore()
    entity_instance = get_fitnessclub_entity_type_for_entity("ExerciseTable")
    ex = es.get_item_by_composite_key2(composite_key)
    if not ex:
        abort(404)
    
    exid = ex['id']

    # auto‐assign section
    sect = ex['category'] if ex['category'] in [s['name'] for s in w['sections']] else 'strength'
    for s in w['sections']:
        if s['name']==sect:
            s['exercises'].append({
              'id':exid,
              'parameters':{'sets':None,'reps':None,'weight':None, 'time':None,'weight_unit':'lbs', 'tempo': None}
            })
            break

    set_cache_value('current_workout', w)

    return workout_canvas2(context, workout_id)

@bp.route('/builder/<workout_id>/add_workout', methods=['POST'])
@auth.login_required
def add_workout(context=None, workout_id=None):

    current_workout = get_cache_value('current_workout')
    if current_workout:
        if current_workout['id'] != workout_id:
            abort(404)
    else:
        # if there is no workout in the cache, we create a new one
        current_workout = new_workout()
        set_cache_value('current_workout', current_workout)

    # here we get the key of the workout from the query parameters
    # and we look it up in the workouts catalog
    # if it is not found we abort with a 404
    # if it is found we add the workout to the workout
    # and we save the workout to the redis cache
    composite_key_str = request.args.get('key', None)
    composite_key = eval(composite_key_str) if composite_key_str else None
    es = EntityStore()
    
    source_workout = es.get_item_by_composite_key2(composite_key)
    if not source_workout:
        abort(404)
    
    # current_workout is the current workout from the cache
    # source_workout is the workout we are adding to the current workout, i.e. is the source of the exercises
    # we will add the exercises from the source to the current, including the parameters of each exercise
    for src_sect in source_workout['sections']:
        src_sect_name = src_sect['name']
        # find the section in the current workout and add the exercises to it
        for curr_sect in current_workout['sections']:
            if curr_sect['name']==src_sect_name:
                # add the exercises from the wk section to the current workout section
                for ex in src_sect['exercises']:
                    curr_sect['exercises'].append({
                      'id':ex['id'],
                      'parameters':{'sets':ex['parameters'].get('sets', None),
                                    'reps':ex['parameters'].get('reps', None),
                                    'weight':ex['parameters'].get('weight', None),
                                    'time': ex['parameters'].get('time', None),
                                    'weight_unit': ex['parameters'].get('weight_unit', 'lbs'),
                                    'tempo': ex['parameters'].get('tempo', None)}
                    })
                break

    set_cache_value('current_workout', current_workout)
    return workout_canvas2(context, workout_id)


@bp.route('/builder/<workout_id>/remove', methods=['POST'])
@auth.login_required
def remove_exercise(context=None, workout_id=None):

    w = get_cache_value('current_workout')

    exid = request.form['exercise_id']
    for s in w['sections']:
        s['exercises'] = [it for it in s['exercises'] if it['id']!=exid]

    set_cache_value('current_workout', w)
    return workout_canvas2(context, workout_id)

@bp.route('/builder/<workout_id>/updatename', methods=['POST'])
@auth.login_required
def update_workout_name(context=None, workout_id=None):

    w = get_cache_value('current_workout')
    w['name'] = request.form['name']
    set_cache_value('current_workout', w)
    return workout_canvas2(context, workout_id)

@bp.route('/builder/<workout_id>/move', methods=['POST'])
@auth.login_required
def move_exercise(context=None, workout_id=None):

    w = get_cache_value('current_workout')

    exid = request.form['exercise_id']
    to = request.form['to_section']
    # remove from any
    for s in w['sections']:
        s['exercises'] = [it for it in s['exercises'] if it['id']!=exid]
    # add to target
    for s in w['sections']:
        if s['name']==to:
            s['exercises'].append({
              'id':exid,
              'parameters':{'sets':None,'reps':None,'weight':None,'time':None,'weight_unit':'lbs', 'tempo': None}
            })

    set_cache_value('current_workout', w)
    return workout_canvas2(context, workout_id)

@bp.route('/builder/<workout_id>/reorder', methods=['POST'])
@auth.login_required
def reorder_exercises(context=None, workout_id=None):

    w = get_cache_value('current_workout')

    sec = request.form['section']
    order = request.form.getlist('order[]')
    for s in w['sections']:
        if s['name']==sec:
            lookup = {it['id']:it for it in s['exercises']}
            s['exercises'] = [lookup[i] for i in order if i in lookup]
            break

    set_cache_value('current_workout', w)
    
    return workout_canvas2(context, workout_id)

@bp.route('/builder/<workout_id>/update_param', methods=['POST'])
@auth.login_required
def update_param(context=None, workout_id=None):

    w = get_cache_value('current_workout')

    exid  = request.form['exercise_id']
    param = request.form['param']
    value = request.form['value'] or None
    for s in w['sections']:
        for it in s['exercises']:
            if it['id']==exid:
                it['parameters'][param] = value

    set_cache_value('current_workout', w)

    return ('', 204)

@bp.route('/builder/<workout_id>/save', methods=['POST'])
@auth.login_required
def save_workout(context=None, workout_id=None):
    user = context.get('user', None)
    member_id = user.get('sub', None) if user else None   
    if not member_id:
        abort(401)

    WORKOUT_ENTITY_NAME = "WorkoutTable"

    workout = get_cache_value('current_workout')
    if not workout or workout['id'] != workout_id:
        abort(404)

    workout_instance : WorkoutEntity = get_fitnessclub_entity_type_for_entity(WORKOUT_ENTITY_NAME)

    # this is where we save the newly created workout
    print('Saving workout')
    es = EntityStore()
    workout['created_by'] = member_id
    workout['created_ts'] = datetime.now().isoformat()
    workout_instance.initialize(workout)
    es.upsert_item(workout_instance)

    delete_from_cache('current_workout')

    response = make_response('')
    response.headers['HX-Trigger'] = json.dumps({
        "eventListChanged": True,
        "showMessage": { "value" : f"saved workout", "target": "body" }
    })

    return redirect(url_for('workouts.index'), 302, response)


########################################
# displays the exercise library within the workout builder

@bp.route('/builder/exercises')
@auth.login_required
def exercise_listing(context=None):
    workout_id = request.args.get('workout_id', None)
    target = request.args.get('target', None)

    view = request.args.get('view', None)
    if view:
        session['view_preference'] = view
    else:
        view = session.get('view_preference', 'list')

    div_id = target
    entity_name = "ExerciseTable"
    page = int(request.args.get('page', 1))
    page_size = 10
    
    fields_to_display  = get_fitnessclub_listing_fields_for_entity(entity_name)

    filters = get_fitnessclub_entity_filters_for_entity(entity_name)

    if filters:
        filter_func  = get_fitnessclub_filter_func_for_entity(entity_name)
        filter_term_func  = get_fitnessclub_filter_term_func_for_entity(entity_name)
        filter_terms = filter_term_func(request.args)
    else:
        filter_func = None
        filter_terms = None

    entities = get_filtered_entities(entity_name, fields_to_display, filter_func, filter_terms)
    
    total_pages = (len(entities) + page_size - 1) // page_size
    start = (page - 1) * page_size
    end = start + page_size
    current = entities[start:end]

    if not entity_name:
        return "No entity name provided", 404
    entity_type = get_fitnessclub_entity_type_for_entity(entity_name)
    
    return hx_render_template('entity_list_component.html',
                              fields_to_display=fields_to_display,
                              main_content_container=div_id,
                              entities=current,
                              entity_name=entity_name,
                              entity_display_name=entity_type.get_display_name(),
                              filter_terms=filter_terms,
                              args=request.args,
                              page=page,
                              view=view,
                              total_pages=total_pages,
                              filter_dialog_route=f'/workouts/filter-dialog?entity_table={entity_name}&target={target}&workout_id={workout_id}',
                              entities_listing_route=f'/workouts/builder/exercises?entity_table={entity_name}&target={target}&workout_id={workout_id}',
                              entity_view_route=f'/exercises/view?entity_table={entity_name}',
                              entity_action_route=f'/workouts/builder/{workout_id}/add?entity_table={entity_name}',
                              entity_action_route_method='post',
                              entity_action_route_target="canvas",                              
                              entity_action_icon='bi-plus',
                              entity_action_label='Add Exercise',
                              context=context)      

@bp.route('/builder/workouts-listing')
@auth.login_required
def builder_workouts_listing(context=None):
    WORKOUT_ENTITY_NAME = "WorkoutTable"
    workout_id = request.args.get('workout_id', None)    
    page = int(request.args.get('page', 1))
    target = request.args.get('target', None)    

    view = request.args.get('view', None)
    if view:
        session['view_preference'] = view
    else:
        view = session.get('view_preference', 'list')
    div_id = target
    fields_to_display  = get_fitnessclub_listing_fields_for_entity(WORKOUT_ENTITY_NAME)
    filters = get_fitnessclub_entity_filters_for_entity(WORKOUT_ENTITY_NAME)

    if filters:
        filter_func  = get_fitnessclub_filter_func_for_entity(WORKOUT_ENTITY_NAME)
        filter_term_func  = get_fitnessclub_filter_term_func_for_entity(WORKOUT_ENTITY_NAME)
        filter_terms = filter_term_func(request.args)
    else:
        filter_func = None
        filter_terms = None

    entities = get_filtered_entities(WORKOUT_ENTITY_NAME, fields_to_display, filter_func, filter_terms)

    page_size = 10
    total_pages = (len(entities) + page_size - 1) // page_size
    start = (page - 1) * page_size
    end = start + page_size
    current = entities[start:end]

    # displays workouts at the top level
    return render_template(
        "entity_list_component.html",
        entity_name=WORKOUT_ENTITY_NAME,
        main_content_container=div_id,
        fields_to_display=fields_to_display,
        entities=current,
        filter_terms=filter_terms,
        args=request.args,
        page=page,
        view=view,
        total_pages=total_pages,
        entities_listing_route=f'/workouts/builder/workouts-listing?entity_table={WORKOUT_ENTITY_NAME}&target={target}',
        entity_view_route=f'/workouts/viewer/workout?entity_table={WORKOUT_ENTITY_NAME}',
        entity_action_route=f'/workouts/builder/{workout_id}/add_workout?entity_table={WORKOUT_ENTITY_NAME}',
        entity_action_route_method='post',
        entity_action_route_target="canvas",                              
        entity_action_icon='bi-plus',  
        entity_action_label='Add Workout',       
        context=context)

# ── Main exercise reviewer View ─────────────────────────────────────────────
# this will display two panels, the one on the left will be the list of exercises
# and the one on the right will be the details of whatever exercise is selected from the list on the left
# whichever exercise is selected, will be added to the redis cache as the current exercise being reviewed
# the action button on the exercise reviewer list will create a form with the exercise details, and the results
# will targeted for the exercise reviewer details panel

@bp.route('/exercise_reviewer')
@auth.login_required
def exercise_reviewer(context=None):

    return hx_render_template('exercise_reviewer.html',
                              context=context)

@bp.route('/exercise_reviewer_listing')
@auth.login_required
def exercise_reviewer_listing(context=None):
    exercise_id = request.args.get('exercise_id', None)
    target = request.args.get('target', None)

    mobile = request.args.get('mobile', type=bool, default=False)
    div_id = 'reviewer-list-mobile' if mobile else 'reviewer-list'
    target = div_id
    
    # view = request.args.get('view', 'list')
    view = request.args.get('view', None)
    if view:
        session['view_preference'] = view
    else:
        view = session.get('view_preference', 'list')

    entity_name = "ExerciseTable"
    page = int(request.args.get('page', 1))
    page_size = 15
    fields_to_display  = get_fitnessclub_listing_fields_for_entity(entity_name)

    filters = get_fitnessclub_entity_filters_for_entity(entity_name)

    if filters:
        filter_func  = get_fitnessclub_filter_func_for_entity(entity_name)
        filter_term_func  = get_fitnessclub_filter_term_func_for_entity(entity_name)
        filter_terms = filter_term_func(request.args)
    else:
        filter_func = None
        filter_terms = None

    entities = get_filtered_entities(entity_name, fields_to_display, filter_func, filter_terms)
    
    total_pages = (len(entities) + page_size - 1) // page_size
    start = (page - 1) * page_size
    end = start + page_size
    current = entities[start:end]

    if not entity_name:
        return "No entity name provided", 404
    entity_type = get_fitnessclub_entity_type_for_entity(entity_name)
    
    return hx_render_template('entity_list_component.html',
                              fields_to_display=fields_to_display,
                              main_content_container=div_id,
                              entities=current,
                              entity_name=entity_name,
                              entity_display_name=entity_type.get_display_name(),
                              filter_terms=filter_terms,
                              args=request.args,
                              page=page,
                              view=view,
                              total_pages=total_pages,
                              filter_dialog_route=f'/workouts/exercise_reviewer/filter-dialog?entity_table={entity_name}&target={target}',
                              entities_listing_route=f'/workouts/exercise_reviewer_listing?target={target}',
                              entity_view_route=f'/exercises/view?entity_table={entity_name}',
                              entity_action_route=f'/workouts/exercise_reviewer/review?target={target}',
                              entity_action_route_method='post',
                              entity_action_route_target="canvas",                              
                              entity_action_icon='bi-arrow-right-square-fill',                            
                              context=context)      

@bp.route('/exercise_reviewer/filter-dialog')
@auth.login_required
def exercise_reviewer_filter_dialog(context=None):
    target = request.args.get('target', None)
    entity_name = "ExerciseTable"
    entity_type = get_fitnessclub_entity_type_for_entity(entity_name)
    filters = get_fitnessclub_entity_filters_for_entity(entity_name)

    return hx_render_template('filter_dialog.html', 
                              entities_listing_route=f'/workouts/exercise_reviewer_listing?target={target}',
                              filter_results_target=target,
                              entity_display_name=entity_type.get_display_name(),                              
                              entity_name=entity_name,
                              filters=filters,
                              args=request.args,
                              context=context)

@bp.route('/exercise_reviewer/review', methods=['POST'])
@auth.login_required
def exercise_reviewer_review(context=None):

    composite_key_str = request.args.get('key', None)
    composite_key = eval(composite_key_str) if composite_key_str else None
    es = EntityStore()

    ex = es.get_item_by_composite_key2(composite_key)
    if not ex:
        abort(404)
    
    exercise_id = ex['id']

    set_cache_value('current_exercise_being_reviewed', ex)

    return exercise_reviewer_editor_canvas2(context, exercise_id)


@bp.route('/exercise_reviewer/<exercise_id>/canvas')
@auth.login_required
def exercise_reviewer_editor_canvas(context=None, exercise_id=None):
    return exercise_reviewer_editor_canvas2(context, exercise_id)

def exercise_reviewer_editor_canvas2(context=None, exercise_id=None):
    es = EntityStore()

    exercise =  get_cache_value('current_exercise_being_reviewed')
    if not exercise:
        abort(404)

    exercise_id = exercise['id']
    
    er = ExerciseReviewEntity({ "id": exercise_id })
    exercise_review = es.get_item(er)
    if not exercise_review:
        exercise_review = ExerciseReviewEntity({ "id": exercise_id })
        es.upsert_item(exercise_review)

    return hx_render_template('exercise_reviewer_editor_canvas.html',
                            exercise=exercise,
                            exercise_review=exercise_review,
                            exercise_review_schema=exercise_review.get_schema(),
                            update_entity_url=url_for('workouts.update_exercise_review')
                            )


@bp.route('/exercise_reviewer/updatereview', methods=['POST'])
@auth.login_required
def update_exercise_review(context=None):
    table_id = "ExerciseReviewTable"
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Invalid or missing JSON"}), 400

    print(f"Received JSON payload for table {table_id}: {data}")
    entity = get_fitnessclub_entity_type_for_entity(table_id)        

    es = EntityStore()
    
    # this assumes that the entity uses 'id' as the key field
    # it also assumes that the entity has a fixed partition value
    # probably need to make this more generic in the future
    # TODO: fix this to be more generic

    entity.initialize(data)
    es.upsert_item(entity)

    response = make_response('')
    response.headers['HX-Trigger'] = json.dumps({
        "entityListChanged": True,
        "showMessage": { "value": f"item was saved.", "target": "body" }
    })

    return response


@bp.route('/exercise_reviewer/<exercise_id>/updatename', methods=['POST'])
@auth.login_required
def update_exercise_name(context=None, exercise_id=None):

    ex = get_cache_value('current_exercise_being_reviewed')
    if not ex:
        abort(404)    
    ex['name'] = request.form['name']

    set_cache_value('current_exercise_being_reviewed', ex)

    return exercise_reviewer_editor_canvas2(context, exercise_id)


@bp.route('/exercise_reviewer/save', methods=['POST'])
@auth.login_required
def reviewer_save_exercise(context=None):
    EXERCISE_ENTITY_NAME= "ExerciseTable"
    user = context.get('user', None)
    member_id = user.get('sub', None) if user else None   
    if not member_id:
        abort(401)
    exercise_id = request.form['exercise_id']
    
    ex = get_cache_value('current_exercise_being_reviewed')
    if not ex or ex['id'] != exercise_id:
        abort(404)

    exercise_type : ExerciseEntity = get_fitnessclub_entity_type_for_entity(EXERCISE_ENTITY_NAME)

    print('Saving workout')
    es = EntityStore()
    exercise_type.initialize(ex)
    es.upsert_item(exercise_type)
    delete_from_cache('current_exercise_being_reviewed')

    response = make_response('')
    response.headers['HX-Trigger'] = json.dumps({
        "eventListChanged": True,
        "showMessage": { "value" : f"exercise changes saved", "target": "body" }
    })

    return response


# ── Workout View ────────────────────────────────────────────────

@bp.route("/viewer/workout")
@auth.login_required
def view_workout(context=None):

    workout_key_str = request.args.get('key', None)
    workout_composite_key = eval(workout_key_str) if workout_key_str else None
    es = EntityStore()
    entity_instance = get_fitnessclub_entity_type_for_entity("WorkoutTable")
    workout = es.get_item_by_composite_key2(workout_composite_key)
    import json
    # print(json.dumps(workout, indent=4))
    wrkout_exercises = get_exercises_from_workout(workout)
    exercises = { ex.get('id', None): ex for ex in wrkout_exercises }
    print(json.dumps(exercises, indent=4))

    if not workout:
        abort(404)
    # new: only use the session value if it exists
    last = session.get(f"last_section_{workout_key_str}")  # no fallback
    return render_template(
        "workout_view.html",
        workout=workout,
        exercises=exercises,
        default_section=last,
        show_finish_button=False
    )

from common.fitness.entities_getter import get_entity

@bp.route("/viewer/workout/<workout_id>/section/<section_name>")
@auth.login_required
def view_section(context=None, workout_id=None, section_name=None):
    workout = get_entity("WorkoutTable", workout_id)
    exercises = get_exercises_from_workout(workout)
    if not workout:
        abort(404)
    section = next((s for s in workout["sections"] if s["name"] == section_name), None)
    if not section:
        abort(404)
    # Persist the user’s current section in session
    session[f"last_section_{workout_id}"] = section_name
    return render_template("_section_view.html",
                           section=section,
                           exercises=exercises)

# @bp.route("/viewer/workout/<workout_id>/finish", methods=["POST"])
# @auth.login_required
# def finish_workout(context=None, workout_id=None):
#     # Called when the workout is done
#     session.pop(f"last_section_{workout_id}", None)
#     return redirect(url_for("view_workout", key=workout_id))

@bp.route("/viewer/workout/<workout_id>/set_section/<section_name>", methods=["POST"])
@auth.login_required
def set_last_section(context=None, workout_id=None, section_name=None):
    # guard: make sure section_name is valid for this workout_id…
    session[f"last_section_{workout_id}"] = section_name
    return ("", 204)

@bp.route("/viewer/exercise/<exercise_id>/details")
@auth.login_required
def exercise_details(context=None, exercise_id=None):
    exercise = get_entity("ExerciseTable", exercise_id)
    allow_popups = request.args.get("allow_popups", default='false')
    # exercise = exercises.get(exercise_id)
    if not exercise:
        abort(404)
    # Render only the drill-in partial
    return render_template("_exercise_details_view.html",
                           exercise=exercise,
                           allow_popups=allow_popups, context=context)

@bp.route("/viewer/exercise/<exercise_id>/feedback", methods=["POST"])
@auth.login_required
def exercise_feedback(context=None, exercise_id=None):
    workout_id = request.args.get("workout_id", None)
    exercise = get_entity("ExerciseTable", exercise_id)
    if not exercise:
        abort(404)
    data = request.get_json(silent=True) or {}
    adjust = request.form.get("adjust")
    # adjust = data.get("adjust")
    # TODO: record feedback (e.g. save to DB, adjust next workout)
    current_app.logger.info(f"Feedback for {exercise_id}: {adjust!r}")
    # We return no content, HTMX hx-swap="none" will leave UI untouched
    return ("", 204)

@bp.route('/view_workout_detail')
@auth.login_required
def view_workout_detail(context):
    es = EntityStore()
    workout_key_str = request.args.get("workout_key", None)
    workout_key = eval(workout_key_str) if workout_key_str else None
    workout = es.get_item_by_composite_key2(workout_key)
    wrkout_exercises = get_exercises_from_workout(workout)
    exercises = { ex.get('id', None): ex for ex in wrkout_exercises }

    # parse ISO timestamp → datetime for nicer formatting
    workout['Timestamp'] = datetime.fromisoformat(workout['Timestamp'])
    # {{ workout.Timestamp.strftime('%A, %B %d, %Y at %-I:%M %p') }}
    return render_template(
        'workout_detail.html',
        workout=workout,
        exercises=exercises
    )