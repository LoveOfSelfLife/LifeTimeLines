from datetime import datetime
from flask import Blueprint, jsonify, make_response, render_template, request, current_app
from common.entity_store import EntityStore
from common.fitness.active_fitness_registry import get_fitnessclub_entity_filters_for_entity, get_entity_obj_from_entity_name, get_fitnessclub_listing_fields_for_entity
from common.fitness.cacher import get_cache_value, set_cache_value, delete_from_cache
from common.fitness.entities_getter import get_entities
from common.fitness.exercise_entity import ExerciseEntity
from common.fitness.exercise_parameters import get_editor_type_for_unit_parameter, get_editor_type_for_value_parameter
from common.fitness.hx_common import get_filter_terms_from_request, hx_render_template
from common.fitness.hx_common import rm_spaces
from common.fitness.member_entity import get_member_id_from_user_context, is_member_an_admin
from common.fitness.member_workout_entity import WorkoutDefinitionEntity, get_exercises_from_workout, map_exercise_to_sections
from common.fitness.edit_workout_object import edit_workout_object
from common.fitness.programs import get_last_workout_instance_for_workout
from common.fitness.programs import get_last_workout_instance_for_workout
from common.fitness.workout_state import get_active_workout_state, update_active_workout_state

bp = Blueprint('workouts', __name__, template_folder='templates')
from auth import auth
from flask import Flask, render_template, request, redirect, url_for, session, abort
import uuid
import json
from common.fitness.exercise_entity import ExerciseEntity, ExerciseReviewEntity

from common.fitness.entities_getter import get_entities, get_entity, get_filtered_entities
from common.fitness.entity_constants import WORKOUT_ENTITY_NAME, WORKOUT_SECTIONS

def new_workout(name='New Workout'):
    wid = str(uuid.uuid4())
    return {
        'id': wid,
        'name': name,
        WORKOUT_SECTIONS: [
            {'name':'warmup','exercises':[]},
            {'name':'ramp','exercises':[]},
            {'name':'core','exercises':[]},
            {'name':'power','exercises':[]},            
            {'name':'core-power','exercises':[]},
            {'name':'combination','exercises':[]},
            {'name':'strength','exercises':[]},
            {'name':'resistance','exercises':[]},
            {'name':'cardio','exercises':[]}
        ]
    }

# ──────────────────────────────────────────────────
@bp.route('/')
@auth.login_required
def index(context=None):
    member_id = get_member_id_from_user_context(context)
    if not member_id:
        abort(401)
    page = int(request.args.get('page', 1))
    filter_terms = get_filter_terms_from_request()    
    return workouts_listing2(context, page, filter_terms)

@bp.route('/workouts-listing', methods=['GET', 'POST'])
@auth.login_required
def workouts_listing(context=None):
    member_id = get_member_id_from_user_context(context)
    if not member_id:
        abort(401)
    page = int(request.args.get('page', 1))
    filter_terms = get_filter_terms_from_request()
    return workouts_listing2(context, page, filter_terms)

def workouts_listing2(context=None, page=1, filter_terms=[]):
    entity_name = WORKOUT_ENTITY_NAME
    member_id = get_member_id_from_user_context(context)
    if not member_id:
        abort(401)

    target = request.args.get('target', None)
    # Handle view preference
    view = (request.form.get('view') if request.method == 'POST' 
            else request.args.get('view')) or session.get('view_preference', 'list')
    
    if view != session.get('view_preference'):
        session['view_preference'] = view
    
    fields_to_display = get_fitnessclub_listing_fields_for_entity(entity_name)
    entities = get_entities(entity_name, fields_to_display, filter_terms, member_id=member_id)
    return workouts_listing_base(context, entity_name, page, target, view, fields_to_display, filter_terms, entities)

def workouts_listing_base(context, entity_name, page, target, view, fields_to_display, filter_terms, entities):
    page_size = 100
    total_pages = (len(entities) + page_size - 1) // page_size
    start = (page - 1) * page_size
    end = start + page_size
    current = entities[start:end]

    if request.headers.get('HX-Target') == 'results-area':
        template_file_name = 'entity_results_partial.html'
    else:
        template_file_name = 'entity_list_component.html'

    # Set results_target_container based on target parameter
    results_target_container = target if target else 'results-area'
    target = target if target else 'results-area'
    # displays workouts at the top level
    return hx_render_template(
        template_file_name,
        entity_name=entity_name,
        title="Workouts Library",
        main_content_container="entities-container",        
        fields_to_display=fields_to_display,
        entities=current,
        filter_terms=filter_terms,
        args=request.args,
        page=page,
        view=view,
        total_pages=total_pages,
        entity_add_route=f"{url_for('workouts.builder_new')}?x=1",
        entities_listing_route=f'/workouts/workouts-listing?entity_table={entity_name}&target={target}',
        entity_view_route=f'/workouts/viewer/workout?entity_table={entity_name}',
        entity_action_route=f'/workouts/edit?entity_table={entity_name}',
        entity_action_icon='bi-pencil-square',  
        entity_action_label='Edit Workout',
        results_target_container=results_target_container,
        # filter_dialog_route=f'/exercises/filter-dialog?entity_table={WORKOUT_ENTITY_NAME}',
        entity_card_view_html='workout_card_view.html',        
        context=context)

@bp.route('/filter-dialog')
@auth.login_required
def filter_dialog(context=None):
    target = request.args.get('target', None)
    workout_id = request.args.get('workout_id', None)
    entity_name = "ExerciseTable"
    entity_type = get_entity_obj_from_entity_name(entity_name)
    filters = get_fitnessclub_entity_filters_for_entity(entity_name)

    return hx_render_template('filter_dialog.html', 
                              entities_listing_route=f'/workouts/builder/exercises?target={target}&workout_id={workout_id}',
                              filter_results_target=target,
                              entity_display_name=entity_type.get_display_name(),                              
                              entity_name=entity_name,
                              filters=filters,
                              args=request.args,
                              context=context)


@bp.route('/edit')
@auth.login_required
def edit_workout_details(context=None):
    composite_key_str = request.args.get('key', None)
    composite_key = eval(composite_key_str) if composite_key_str else None
    es = EntityStore()
    w = es.get_item_by_composite_key(composite_key)
    workout_to_edit = get_entity_obj_from_entity_name(WORKOUT_ENTITY_NAME)
    workout_to_edit.initialize(w)
    # print(f"editing workoug: {json.dumps(workout_to_edit, indent=4)}")
    return edit_workout_object(workout_to_edit)
    
@bp.route('/copy', methods=['POST'])
@auth.login_required
def copy_workout(context=None):
    """Copy an existing workout"""
    member_id = get_member_id_from_user_context(context)
    if not member_id:
        abort(401)
    
    composite_key_str = request.args.get('key', None)
    composite_key = eval(composite_key_str) if composite_key_str else None
    
    es = EntityStore()
    original_workout = es.get_item_by_composite_key(composite_key)
    if not original_workout:
        abort(404)

    # Create copy with new ID and modified name
    copied_workout = original_workout.copy()
    copied_workout['id'] = str(uuid.uuid4())
    copied_workout['name'] = f"Copy of {original_workout['name']}"
    copied_workout['created_by'] = member_id
    copied_workout['created_ts'] = datetime.now().isoformat()
    
    # Save the copy
    workout_entity = WorkoutDefinitionEntity(copied_workout)
    es.upsert_item(workout_entity)
    
    return edit_workout_object(workout_entity)

@bp.route('/builder/new')
@auth.login_required
def builder_new(context=None):
    w = new_workout()
    return edit_workout_object(w)

# ── Main Builder View ─────────────────────────────────────────────
@bp.route('/builder/<workout_id>')
@auth.login_required
def builder(context=None, workout_id=None):
    member_id = get_member_id_from_user_context(context)
    if not member_id:
        abort(401)

    # this will be set when this workout editor has been opened while editing a workout that is part of a program in the program builder.
    # in that case, we want to load the workout that is being edited as part of the program builder flow, which is stored in the cache 
    # with the key 'editing_program_workout'

    editing_program_workout = request.args.get('editing_program_workout', None)

    workout = get_cache_value('current_workout')

    if workout and workout['id'] == workout_id:
        # Check if current user can save this workout
        can_save_workout = True
        if workout.get('created_by'):
            can_save_workout = (workout.get('created_by') == member_id) or is_member_an_admin(member_id)
        
        return hx_render_template('workout_builder.html', 
                                workout=workout, 
                                context=context, 
                                source='exercises', 
                                editing_program_workout=editing_program_workout,
                                can_save_workout=can_save_workout)


# ── Fragments ────────────────────────────────────────────────────
@bp.route('/builder/<workout_id>/canvas')
@auth.login_required
def workout_canvas(context=None, workout_id=None):
    return workout_canvas2(context, workout_id)

def workout_canvas2(context=None, workout_id=None):
    return workout_dynamic_canvas2(context, workout_id)


def exercise_with_id_has_param(exercise_id, param):
    exercise : ExerciseEntity = get_entity('ExerciseTable', key=exercise_id, partition_key='exercise')
    if not exercise:
        return False
    return exercise_has_param(exercise, param)

def exercise_has_param(exercise, param):
    if param[0] == 'S':
        return not exercise.is_only_one_set()
    if param[0] == 'R':
        return exercise.get_set_completion_measure() == 'reps'
    if param[0] == 'T':
        return exercise.get_set_completion_measure() == 'time'
    if param[0] == 'D':
        return exercise.get_set_completion_measure() == 'distance'
    if param[0] == 'F':
        return exercise.exercises_uses_external_force()
    return False

def get_initial_params_for_exercise():
    return { 'S':'', 'R':'', 'T':'secs', 'Tu':'', 'D':'', 'Du':'ft', 'F':'', 'Fu':'lbs', 'P':'', 'Pu':'' }

def get_parameter_map():
    return {
        'S':  'sets',
        'R':  'reps',
        'T':  'time',
        'Tu': 'time_unit',
        'D':  'distance',
        'Du': 'dist_unit',
        'F':  'resistance',
        'Fu': 'resist_unit',
        'P':  'tempo',
        'Pu': 'tempo_unit'
    }


@bp.route('/builder/update_param_in_cache', methods=['POST'])
@auth.login_required
def update_param_in_cache(context=None):

    w = get_cache_value('current_workout')

    exid  = request.form['exercise_id']
    workout_id = request.form['workout_id']
    param = request.form['param']
    value = request.form['value'] or None
    for s in w[WORKOUT_SECTIONS]:
        for it in s['exercises']:
            if it['id']==exid:
                it['parameters'][param] = value

    set_cache_value('current_workout', w)

    return ('', 204)


@bp.route('/update_param_in_session', methods=['POST'])
@auth.login_required
def update_param_in_session(context=None):

    current_workout_state = get_active_workout_state()
    current_parameters = current_workout_state.get('exercise_parameters', {})

    exid  = request.form['exercise_id']
    param = request.form['param']
    value = request.form['value'] or ''
    if exid not in current_parameters:
        current_parameters[exid] = get_initial_params_for_exercise()
    current_parameters[exid][param] = value
    update_active_workout_state(current_workout_state)

    return ('', 204)

def get_cached_param_value(exercise_id, param):
    w = get_cache_value('current_workout')
    parameters = None
    value = ''
    for s in w[WORKOUT_SECTIONS]:
        for it in s['exercises']:
            if it['id']==exercise_id:
                parameters = it['parameters']
            if parameters:
                break
        if parameters:
            break
    if parameters:
        value = parameters.get(param, '')
    return value

def get_workout_sections(workout):
    if workout:
        return workout.get('sections', []) if 'sections' in workout else workout.get('workout_sections', [])
    return []

def get_workout_section(workout, section_name):
    for sec in get_workout_sections(workout):
        if sec['name'] == section_name:
            return sec
    return None

def get_param_from_session_or_workout(current_parameters, exercise_id, param, workout_obj, default_value=''):
    # First check session parameters
    if current_parameters and exercise_id in current_parameters and param in current_parameters[exercise_id]:
        param_value = current_parameters[exercise_id][param]
        if param_value is None or param_value.strip() == 'None':
            return default_value
        else:
            return param_value
    # Then check workout object parameters
    for sec in get_workout_sections(workout_obj):
        for it in sec['exercises']:
            if it['id']==exercise_id:
                return it['parameters'].get(param, default_value)
    return default_value   

@bp.route('/dynamic_parameters_for_section_viewer/<workout_id>/<section_name>')
@auth.login_required
def dynamic_parameters_for_section_viewer(context=None, workout_id=None, section_name=None):

    # this method as written assumes that the workout parameters are stored in the active_workout_state in the session
    # but when we are editing the parameters of a workout in the program builder, we want to get those parameters from the
    # cache value 'current_workout' instead of the session, since the session is meant to store the state of an active workout that the user is doing, 
    # whereas when we are editing a workout in the program builder, we are not doing that workout, we are just editing the workout object that is stored in the cache.

    # need to determine here if we are actively working out and editing the workout parameters for the workout we are doing, in which case we want to get and update the parameters in the session,
    # or if we are editing a workout in the workout builder, in which case we want to get and update the parameters in the cache.
    # we can determine this based on a flag that is passed in the request args, if editing_program_workout is true, then we are editing the workout in the workout builder, 
    # otherwise we are actively working out and editing the parameters for the workout we are doing.

    editing_program_workout = request.args.get('editing_program_workout', 'false').lower() == 'true'
    purpose_of_parameter_edit = request.args.get("purpose_of_parameter_edit", None)
    active_workout = request.args.get('active_workout', 'false').lower() == 'true'
    workout_instance = None
    workout_definition = None
    
    # if active_workout:
    if editing_program_workout is False:
        # this block is for when we are doing a workout and want to edit the parameters for that workout, in which case we want to get and update the parameters in the session

        es = EntityStore()
        workout_instance_key = request.args.get('workout_instance_key', None)
        workout_definition_key = request.args.get('workout_definition_key', None)
        can_edit=request.args.get('can_edit', 'false').lower() == 'true'
        active_workout=request.args.get('active_workout', 'false').lower() == 'true'

        # TODO:  trying to figure out how to display the parameters of a workout when the user is previewing
        # the workout from the home page dashboard, in which case we want to show the parameters with the adjustments for the next time already applied, 
        # so that they can see exactly what they will be doing in their next workout.
        # on the home page dashboard, when the user clicks on the workout preview, we can set a flag in the request args to indicate that 
        # we want to show the parameters with the adjustments for the next time already applied, and then in this method, if that flag is set, we can get the last workout instance 
        # for that workout and use the parameters from that workout instance instead of the parameters from the workout definition.
        # issue is that searching for the last workout instance is expensive, so may want to do it before we get here and somehow pass it down

        if workout_instance_key:
            workout_instance = es.get_item_by_composite_key(workout_instance_key)

        elif workout_definition_key:
            workout_definition = es.get_item_by_composite_key(workout_definition_key)

        wrkout_exercises = get_exercises_from_workout(workout_instance if workout_instance else workout_definition)
        exercises = { ex.get('id', None): ex for ex in wrkout_exercises }

        current_workout_state = get_active_workout_state()
        current_parameters = current_workout_state.get('exercise_parameters', {}) if current_workout_state else {}
        if purpose_of_parameter_edit == 'finishing_workout_next_time' and current_workout_state:
            current_parameters = current_workout_state.get('adjustments') or current_parameters
        update_url = url_for('workouts.update_param_in_session')

        section = get_workout_section(workout_instance if workout_instance else workout_definition, section_name)

        exercise_parameters_map = extract_workout_parameters_for_workout(workout_id, 
                                                                        workout_instance if workout_instance else workout_definition, 
                                                                        exercises, 
                                                                        current_parameters, 
                                                                        update_url)
        can_edit_parameters = can_edit or workout_instance 

    else:
        # we enter this block when we are viewing the workout in the workout builder and want to edit the parameters for the workout
        # there are situations where this may occur:
        #
        # 1) we are in the workout builder and we want to edit the parameters for the workout we are building.  Any updates to the parameters in this situation
        #    should update the workout object that is stored in the cache with the key 'current_workout'
        #
        # 2) we are in the program builder and we are editing the parameters of a workout that is part of a program, in which case the updates to the parameters
        #    should update the workout object that is stored im current_program_workouts in the cache. (me thinks...)
        if purpose_of_parameter_edit == 'editing_workout_in_program_builder':

            current_program_workouts = get_cache_value('current_program_workouts')
            workout = next((wk for wk in current_program_workouts if wk.get('id', None) == workout_id), None)
            
            if not workout:
                abort(404)
                
        else:
            workout = get_cache_value('current_workout')
            
        exercises = { ex['id']: ex for ex in get_exercises_from_workout(workout) }
        update_url = url_for('workouts.update_param_in_cache')
        section = get_workout_section(workout, section_name)
        exercise_parameters_map = extract_workout_parameters_for_workout(workout_id, workout, exercises, {}, update_url)
        can_edit_parameters = True
        workout_definition = workout
        workout_definition_key = None
        active_workout = False
        


    return render_template(
        "_section_dynamic_view.html",
        workout=workout_instance if workout_instance else workout_definition,
        exercise_parameters=exercise_parameters_map.get(section_name, {}),
        section=section,
        exercises=exercises,
        workout_definition_key=workout_definition_key,
        can_edit_parameters=can_edit_parameters, 
        active_workout=active_workout,
        in_program_builder=editing_program_workout,
        purpose_of_parameter_edit=purpose_of_parameter_edit,
        rs=rm_spaces
    )

def extract_workout_parameters_for_section(workout_id, section_name, workout_obj, exercises, current_parameters, update_url, sections):
    exercise_parameters = {}
    for sec in sections:
        if sec['name'] == section_name:
            section = sec
            for item in sec['exercises']:
                ex = exercises[item['id']]
                exercise_parameters[ex['id']] = { 'param_list': get_param_objects_for_exercise(ex, 
                                                                                               current_parameters, 
                                                                                               workout_obj, 
                                                                                               workout_id, update_url) }
            break
    return exercise_parameters,section

def extract_workout_parameters_for_workout(workout_id, workout_obj, exercises, current_parameters, update_url):
    exercise_parameters_map = {}
    sections = get_workout_sections(workout_obj)
    for sec in sections:
        exercise_parameters_map[sec['name']] = {}
        for item in sec['exercises']:
            ex = exercises[item['id']]
            exercise_parameters_map[sec['name']][ex['id']] = { 'param_list': get_param_objects_for_exercise(ex, 
                                                                                                            current_parameters, 
                                                                                                            workout_obj, 
                                                                                                            workout_id, 
                                                                                                            update_url) }
    return exercise_parameters_map

def get_param_objects_for_exercise(exercise, current_parameters, workout_instance, workout_id, update_url):
    param_objects = []
    # TODO:  this method has a lot of repeated code in it, we should refactor it to be more concise and easier to maintain. 
    # maybe have a config that defines the parameters and their properties, then loop through that config to generate the param objects.

    # TODO:  the default value for a parameter should be based on the exercise definition, not just a hardcoded value, as it is implemented now.  
    if exercise_has_param(exercise, 'S'):
        param_value = get_param_from_session_or_workout(current_parameters, exercise['id'], 'S', workout_instance, default_value='0')
        param_objects.append({
            'type': 'var',
            'value': param_value,
            'update_url': update_url,
            'param': 'S',
            'wkout_id': workout_id,
            'ex_id': exercise['id']
        })
        param_objects.append({
            'type': 'text',
            'value': "sets, "
        })


    if exercise_has_param(exercise, 'R'):
        param_value = get_param_from_session_or_workout(current_parameters, exercise['id'], 'R', workout_instance, default_value='0')
        param_objects.append({
            'type': 'var',
            'value': param_value,
            'update_url': update_url,
            'param': 'R',
            'wkout_id': workout_id,
            'ex_id': exercise['id']
        })
            
        param_objects.append({
            'type': 'text',
            'value': "reps, "
        })

    if exercise_has_param(exercise, 'T'):
        param_value = get_param_from_session_or_workout(current_parameters, exercise['id'], 'T', workout_instance, default_value='0')
        # if param_value:
        param_objects.append({
            'type': 'var',
            'value': param_value,
            'update_url': update_url,
            'param': 'T',
            'wkout_id': workout_id,
            'ex_id': exercise['id']
        })
        param_value = get_param_from_session_or_workout(current_parameters, exercise['id'], 'Tu', workout_instance, default_value='sec')
        param_objects.append({
            'type': 'var',
            'value': param_value,
            'update_url': update_url,
            'param': 'Tu',
            'wkout_id': workout_id,
            'ex_id': exercise['id']
        })

    if exercise_has_param(exercise, 'D'):
        
        param_value = get_param_from_session_or_workout(current_parameters, exercise['id'], 'D', workout_instance, default_value='0')
        # if param_value: 
        param_objects.append({
            'type': 'var',
            'value': param_value,
            'update_url': update_url,
            'param': 'D',
            'wkout_id': workout_id,
            'ex_id': exercise['id']
        })
        param_value = get_param_from_session_or_workout(current_parameters, exercise['id'], 'Du', workout_instance, default_value='meters')
        param_objects.append({
            'type': 'var',
            'value': param_value,
            'update_url': update_url,
            'param': 'Du',
            'wkout_id': workout_id,
            'ex_id': exercise['id']
        })

    if exercise_has_param(exercise, 'F'):
        param_value = get_param_from_session_or_workout(current_parameters, exercise['id'], 'F', workout_instance, default_value='0')
        # if param_value:
        param_objects.append({
            'type': 'var',
            'value': param_value,
            'update_url': update_url,
            'param': 'F',
            'wkout_id': workout_id,
            'ex_id': exercise['id']
        })
        param_value = get_param_from_session_or_workout(current_parameters, exercise['id'], 'Fu', workout_instance, default_value='lbs')
        param_objects.append({
            'type': 'var',
            'value': param_value,
            'update_url': update_url,
            'param': 'Fu',
            'wkout_id': workout_id,
            'ex_id': exercise['id']
        })
    return param_objects



@bp.route('/builder/<workout_id>/dynamic_canvas')
@auth.login_required
def workout_dynamic_canvas(context=None, workout_id=None):
    return workout_dynamic_canvas2(context, workout_id)

def workout_dynamic_canvas2(context=None, workout_id=None):
    w =  get_cache_value('current_workout')
    if w:
        wrkout_exercises = get_exercises_from_workout(w)
        exercises = { ex.get('id', None): ex for ex in wrkout_exercises }
        exercise_parameters_map = extract_workout_parameters_for_workout(workout_id, w, exercises, {}, url_for('workouts.update_param_in_cache'))
        return hx_render_template('_workout_dynamic_canvas.html',
                                    workout=w,
                                    exercises=exercises,
                                    exercise_parameters = exercise_parameters_map,
                                    workout_id=workout_id,
                                    purpose_of_parameter_edit='workout_builder',
                                    can_edit_parameters=True,
                                    context=context)
    else:
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
    entity_instance = get_entity_obj_from_entity_name("ExerciseTable")
    ex = es.get_item_by_composite_key(composite_key)
    if not ex:
        abort(404)
    
    exid = ex['id']
    # this returns the list of potential sections that the exercise should go into
    secs = map_exercise_to_sections(ex)
    
    if secs:
        # check all the sections of the workout and add the exercise to first section that matches one of the potential sections for the exercise
        added = False
        for s in w[WORKOUT_SECTIONS]:
            if s['name'] in secs:
                s['exercises'].append({
                  'id':exid,
                  'parameters':get_initial_params_for_exercise()
                })
                added = True
                break
            
        if not added:
            # given that no section was found in the workout that matches one of the potential sections for the exercise,
            # choose the first potential section and add the exercise to that section (creating the section if it does not exist in the workout)
            section = secs[0]
            w[WORKOUT_SECTIONS].append({
                'name': section,
                'exercises': [{
                  'id':exid,
                  'parameters':get_initial_params_for_exercise()
                }]
            })
    else:
        # add the exercise to the first section, but first check if there is a section named the same as the exercise category and add it there instead
        if len(w[WORKOUT_SECTIONS]) > 0:
            w[WORKOUT_SECTIONS][0]['exercises'].append({
              'id':exid,
              'parameters':get_initial_params_for_exercise()
            })
        else:
            w[WORKOUT_SECTIONS].append({
                'name': 'general',
                'exercises': [{
                  'id':exid,
                  'parameters':get_initial_params_for_exercise()
                }]
            })
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
    
    source_workout = es.get_item_by_composite_key(composite_key)
    if not source_workout:
        abort(404)
    
    # current_workout is the current workout from the cache
    # source_workout is the workout we are adding to the current workout, i.e. is the source of the exercises
    # we will add the exercises from the source to the current, including the parameters of each exercise
    for src_sect in source_workout[WORKOUT_SECTIONS]:
        src_sect_name = src_sect['name']
        # find the section in the current workout and add the exercises to it
        for curr_sect in current_workout[WORKOUT_SECTIONS]:
            if curr_sect['name']==src_sect_name:
                # add the exercises from the wk section to the current workout section
                for ex in src_sect['exercises']:
                    curr_sect['exercises'].append({
                      'id':ex['id'],
                      'parameters':{'S':ex['parameters'].get('S', ''),
                                    'R':ex['parameters'].get('R', ''),
                                    'T':ex['parameters'].get('T', 'secs'),
                                    'Tu':ex['parameters'].get('Tu', ''),
                                    'D':ex['parameters'].get('D', ''),
                                    'Du':ex['parameters'].get('Du', 'ft'),
                                    'F':ex['parameters'].get('F', ''),
                                    'Fu':ex['parameters'].get('Fu', 'lbs'),
                                    'P':ex['parameters'].get('P', ''),
                                    'Pu':ex['parameters'].get('Pu', '')}
                    })
                break

    set_cache_value('current_workout', current_workout)
    return workout_canvas2(context, workout_id)


@bp.route('/builder/<workout_id>/remove', methods=['POST'])
@auth.login_required
def remove_exercise(context=None, workout_id=None):

    w = get_cache_value('current_workout')

    exid = request.form['exercise_id']
    for s in w[WORKOUT_SECTIONS]:
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
    for s in w[WORKOUT_SECTIONS]:
        s['exercises'] = [it for it in s['exercises'] if it['id']!=exid]
    # add to target
    for s in w[WORKOUT_SECTIONS]:
        if s['name']==to:
            s['exercises'].append({
              'id':exid,
              'parameters':get_initial_params_for_exercise()
            })

    set_cache_value('current_workout', w)
    return workout_canvas2(context, workout_id)

@bp.route('/builder/<workout_id>/reorder', methods=['POST'])
@auth.login_required
def reorder_exercises(context=None, workout_id=None):

    w = get_cache_value('current_workout')

    sec = request.form['section']
    order = request.form.getlist('order[]')
    for s in w[WORKOUT_SECTIONS]:
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
    for s in w[WORKOUT_SECTIONS]:
        for it in s['exercises']:
            if it['id']==exid:
                it['parameters'][param] = value

    set_cache_value('current_workout', w)

    return ('', 204)

@bp.route("/update-workout-param-value/<workout_id>/<exercise_id>/<param>", methods=["PUT"])
def save_data(workout_id, exercise_id, param, context=None):
    orig_value = request.form.get("orig_param_value", "")
    new_value = request.form.get("new-param-value", "")
    is_active_workout = request.form.get("active_workout", "false").lower() == "true"
    unit_param_value = request.form.get("unit_param_value", "")
    purpose_of_parameter_edit = request.args.get("purpose_of_parameter_edit", None)
    unit_param_id = request.form.get("unit_param_id", None)

    # if the new_value is empty of just whitespace, then revert back to the original value
    if not new_value or not new_value.strip():
        new_value = orig_value

    # Here you would typically save the new value to your database
    print(f"Saving new value for workout {workout_id}, exercise {exercise_id}, param {param}: '{orig_value}' -> '{new_value}'")

    if is_active_workout:
        print(f"Active workout flag is set. This means the user is currently doing the workout and we should update the workout state in the session with the new parameter value for real-time tracking and analytics purposes.")
        current_workout_state = get_active_workout_state()
        if not current_workout_state:
            print("No active workout state found in session. This should not happen if the active workout flag is set. Aborting update.")
            return ('', 400)

        exercise = current_workout_state['exercise_parameters'].get(exercise_id, {})
        exercise[param] = new_value
        current_workout_state['exercise_parameters'][exercise_id] = exercise

        update_active_workout_state(current_workout_state)

    else:
        print(f"Active workout flag is not set. This means the user is editing the workout in the workout builder and we should update the workout in the cache with the new parameter value so that it is reflected in the workout builder view.")

        if purpose_of_parameter_edit == "finishing_workout_next_time":
            current_workout_state = get_active_workout_state()
            if not current_workout_state:
                print("No active workout state found in session while saving next-time workout adjustments. Aborting update.")
                return ('', 400)

            adjustments = current_workout_state.get('adjustments', {})
            exercise = adjustments.get(exercise_id)
            if exercise is None:
                exercise = current_workout_state.get('exercise_parameters', {}).get(exercise_id, {}).copy()
            exercise[param] = new_value
            adjustments[exercise_id] = exercise
            current_workout_state['adjustments'] = adjustments
            update_active_workout_state(current_workout_state)

        elif purpose_of_parameter_edit == "editing_workout_in_program_builder":
            print(f"Purpose of parameter edit is editing_workout_in_program_builder. This means we are editing a workout that is part of a program in the program builder, so we need to update the workout object that is stored in current_program_workouts in the cache with the new parameter value.")
            current_program_workouts = get_cache_value('current_program_workouts')
            if not current_program_workouts:
                print("No current program workouts found in cache. This should not happen if we are editing a workout in the program builder. Aborting update.")
                return ('', 400)

            for wk in current_program_workouts:
                if wk['id'] == workout_id:
                    for s in wk[WORKOUT_SECTIONS]:
                        for it in s['exercises']:
                            if it['id']==exercise_id:
                                it['parameters'][param] = new_value
                    break
            set_cache_value('current_program_workouts', current_program_workouts)
            
        else:
            w = get_cache_value('current_workout')
            if w:   
                for s in w[WORKOUT_SECTIONS]:
                    for it in s['exercises']:
                        if it['id']==exercise_id:
                            it['parameters'][param] = new_value

                set_cache_value('current_workout', w)

    # Return the updated content to replace the form
    return  get_initial_editable_text2(workout_id, exercise_id, param, new_value, active_workout=is_active_workout, purpose_of_parameter_edit=purpose_of_parameter_edit)

@bp.route('/builder/<workout_id>/save', methods=['POST'])
@auth.login_required
def save_workout(context=None, workout_id=None):
    member_id = get_member_id_from_user_context(context)
    if not member_id:
        abort(401)
    
    WORKOUT_ENTITY_NAME = WorkoutDefinitionEntity.table_name

    workout = get_cache_value('current_workout')
    if not workout or workout['id'] != workout_id:
        abort(404)

    workout_instance : WorkoutDefinitionEntity = get_entity_obj_from_entity_name(WORKOUT_ENTITY_NAME)

    # this is where we save the newly created workout
    print('Saving workout')
    es = EntityStore()
    workout['created_by'] = member_id
    workout['created_ts'] = datetime.now().isoformat()
    workout_instance.initialize(workout)
    es.upsert_item(workout_instance)

    delete_from_cache('current_workout')

    member_id = get_member_id_from_user_context(context)
    if not member_id:
        abort(401)

    response = make_response(workouts_listing2(context))
    response.headers['HX-Trigger'] = json.dumps({
        "eventListChanged": { "target": "body" },
            "showMessage": { 
            "target": "body",
            "value": "workout saved." }
        })     
    return response

@bp.route('/builder/<workout_id>/cancel-editing', methods=['POST'])
@auth.login_required
def cancel_editing_workout(context=None, workout_id=None):
    editing_program_workout = get_cache_value('workout_editor_context')
    if editing_program_workout and editing_program_workout.get('editing_program_workout', None) is not None:
        delete_from_cache('workout_editor_context')
        return redirect(url_for('program.builder'))
    else:
        delete_from_cache('current_workout')
        return redirect(url_for('workouts.index'))

# this is the route we use to save a workout that is part of a program, i.e. a workout that is being edited from within the program view. 
# When we save a workout from within the program view we want to replace the workout in the cached list of program workouts with the newly saved workout, 
# so that when we return to the program view the updated workout is displayed in the program canvas.
# we also do NOT want to persist this workout yet, because the workout is still being edited within the program and we only want to persist the workout when the user saves the program.
@bp.route('/builder/<workout_id>/save-program-workout', methods=['POST'])
@auth.login_required
def save_program_workout(context=None, workout_id=None):
    member_id = get_member_id_from_user_context(context)
    if not member_id:
        abort(401)
    
    workout = get_cache_value('current_workout')
    if not workout or workout['id'] != workout_id:
        abort(404)

    current_program_workouts = get_cache_value('current_program_workouts')

    for idx, wk in enumerate(current_program_workouts):
        if wk['id'] == workout_id:
            current_program_workouts[idx] = workout  # replace the workout in the cached list of program workouts with the newly saved workout
            set_cache_value('current_program_workouts', current_program_workouts)  # update the cache with the modified list of program workouts
            break
    delete_from_cache('workout_editor_context') # clear the workout editor context from the cache since we are done editing the workout within the program context
    return redirect(url_for('program.builder'))

@bp.route('/builder/<workout_id>/save_copy', methods=['POST'])
@auth.login_required
def save_workout_copy(context=None, workout_id=None):
    member_id =get_member_id_from_user_context(context)
    if not member_id:
        abort(401)

    workout = get_cache_value('current_workout')
    if not workout or workout['id'] != workout_id:
        abort(404)

    workout_definition : WorkoutDefinitionEntity = get_entity_obj_from_entity_name(WorkoutDefinitionEntity.table_name)

    # this is where we save the newly created workout
    print('Saving workout copy')
    es = EntityStore()
    workout['id'] = str(uuid.uuid4())
    workout['name'] = f"Copy of {workout['name']}"
    workout['created_by'] = member_id
    workout['created_ts'] = datetime.now().isoformat()
    workout_definition.initialize(workout)
    es.upsert_item(workout_definition)

    delete_from_cache('current_workout')

    member_id = get_member_id_from_user_context(context)
    if not member_id:
        abort(401)
    
    response = make_response(workouts_listing2(context))
    response.headers['HX-Trigger'] = json.dumps({
        "eventListChanged": { "target": "body" },
            "showMessage": { 
            "target": "body",
            "value": "copy of workout saved." }
        })
    return response


########################################
# displays the exercise library within the workout builder

@bp.route('/builder/exercises', methods=['GET', 'POST'])
@auth.login_required
def exercise_listing(context=None):
    workout_id = request.args.get('workout_id', None)
    target = request.args.get('target', None)
    div_id = target
    entity_name = "ExerciseTable"
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
 
    
    fields_to_display  = get_fitnessclub_listing_fields_for_entity(entity_name)

    fields_to_display = get_fitnessclub_listing_fields_for_entity(entity_name)
    filter_terms = get_filter_terms_from_request()
    entities = get_entities(entity_name, fields_to_display, filter_terms, member_id=member_id)
    
    total_pages = (len(entities) + page_size - 1) // page_size
    start = (page - 1) * page_size
    end = start + page_size
    current = entities[start:end]

    if not entity_name:
        return "No entity name provided", 404
    entity_type = get_entity_obj_from_entity_name(entity_name)
    if request.headers.get('HX-Target') in ['results-area']:
        template_file_name = 'entity_results_partial.html'
    else:
        template_file_name = 'entity_list_component.html'

    return hx_render_template(template_file_name,
                              fields_to_display=fields_to_display,
                              title="Exercises Library",                              
                              main_content_container='xyz',
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
                              results_target_container=target if target else 'results-area',
                              context=context,
                              entity_card_view_html='exercise_card_view.html'                                      
                              )      

########################################
# displays the workouts library within the workout builder

@bp.route('/builder/workouts-listing', methods=['GET', 'POST'])
@auth.login_required
def builder_workouts_listing(context=None):
    entity_name = WORKOUT_ENTITY_NAME
    workout_id = request.args.get('workout_id', None)    
    page = int(request.args.get('page', 1))
    target = request.args.get('target', None)    
    member_id = get_member_id_from_user_context(context)
    view = request.args.get('view', None)
    if view:
        session['view_preference'] = view
    else:
        view = session.get('view_preference', 'list')
    div_id = target

    # Handle view preference
    view = (request.form.get('view') if request.method == 'POST' 
            else request.args.get('view')) or session.get('view_preference', 'list')
    
    if view != session.get('view_preference'):
        session['view_preference'] = view
    
    fields_to_display = get_fitnessclub_listing_fields_for_entity(entity_name)
    filter_terms = get_filter_terms_from_request()
    entities = get_entities(entity_name, fields_to_display, filter_terms, member_id=member_id)

    page_size = 100
    total_pages = (len(entities) + page_size - 1) // page_size
    start = (page - 1) * page_size
    end = start + page_size
    current = entities[start:end]

    if request.headers.get('HX-Target') == 'results-area':
        template_file_name = 'entity_results_partial.html'
    else:
        template_file_name = 'entity_list_component.html'

    # displays workouts at the top level
    return render_template(template_file_name,
        entity_name=entity_name,
        title="Workouts Library",
        main_content_container= 'xyz',
        fields_to_display=fields_to_display,
        entities=current,
        filter_terms=filter_terms,
        args=request.args,
        page=page,
        view=view,
        total_pages=total_pages,
        entities_listing_route=f'/workouts/builder/workouts-listing?entity_table={entity_name}&target={target}&workout_id={workout_id}',
        entity_view_route=f'/workouts/viewer/workout?entity_table={entity_name}',
        entity_action_route=f'/workouts/builder/{workout_id}/add_workout?entity_table={entity_name}',
        entity_action_route_method='post',
        entity_action_route_target="canvas",                              
        entity_action_icon='bi-plus',  
        entity_action_label='Add Workout',
        results_target_container=target if target else 'results-area',
        entity_card_view_html='workout_card_view.html',
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

@bp.route('/exercise_reviewer_listing', methods=['GET', 'POST'])
@auth.login_required
def exercise_reviewer_listing(context=None):
    exercise_id = request.args.get('exercise_id', None)
    target = request.args.get('target', None)

    mobile = request.args.get('mobile', type=bool, default=False)
    div_id = 'reviewer-list-mobile' if mobile else 'reviewer-list'
    target = div_id
    member_id = get_member_id_from_user_context(context)
    if not member_id:
        abort(401)    
    entity_name = "ExerciseTable"
    page = int(request.args.get('page', 1))
    page_size = 100

    # Handle view preference
    view = (request.form.get('view') if request.method == 'POST' 
            else request.args.get('view')) or session.get('view_preference', 'list')
    
    if view != session.get('view_preference'):
        session['view_preference'] = view
    
    fields_to_display = get_fitnessclub_listing_fields_for_entity(entity_name)
    filter_terms = get_filter_terms_from_request()
    entities = get_entities(entity_name, fields_to_display, filter_terms, member_id=member_id)
    
    total_pages = (len(entities) + page_size - 1) // page_size
    start = (page - 1) * page_size
    end = start + page_size
    current = entities[start:end]

    if not entity_name:
        return "No entity name provided", 404
    entity_type = get_entity_obj_from_entity_name(entity_name)

    if request.headers.get('HX-Target') == 'results-area':
        template_file_name = 'entity_results_partial.html'
    else:
        template_file_name = 'entity_list_component.html'

    return hx_render_template(template_file_name,
                              fields_to_display=fields_to_display,
                              main_content_container='xyz',
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
                              results_target_container=target if target else 'results-area',
                              context=context)      

@bp.route('/exercise_reviewer/filter-dialog')
@auth.login_required
def exercise_reviewer_filter_dialog(context=None):
    target = request.args.get('target', None)
    entity_name = "ExerciseTable"
    entity_type = get_entity_obj_from_entity_name(entity_name)
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

    ex = es.get_item_by_composite_key(composite_key)
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
    entity = get_entity_obj_from_entity_name(table_id)        

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
    member_id = get_member_id_from_user_context(context)
    if not member_id:
        abort(401)
    exercise_id = request.form['exercise_id']
    
    ex = get_cache_value('current_exercise_being_reviewed')
    if not ex or ex['id'] != exercise_id:
        abort(404)

    exercise_type : ExerciseEntity = get_entity_obj_from_entity_name(EXERCISE_ENTITY_NAME)

    print('Saving workout')
    es = EntityStore()
    exercise_type.initialize(ex)
    es.upsert_item(exercise_type)
    delete_from_cache('current_exercise_being_reviewed')

    response = make_response('')
    response.headers['HX-Trigger'] = json.dumps({
        "eventListChanged": True,
        "showMessage": { "value" : "exercise saved", "target": "body" }
    })

    return response


# ── Workout View ────────────────────────────────────────────────

@bp.route("/viewer/workout")
@auth.login_required
def view_workout(context=None):

    workout_key_str = request.args.get('key', None)
    is_modal = request.args.get('is_modal', 'false').lower() == 'true'

    workout_composite_key = eval(workout_key_str) if workout_key_str else None
    es = EntityStore()

    workout = es.get_item_by_composite_key(workout_composite_key)

    # if we are previewing the workout from the home page dashboard, then we want to 
    # use the last instance of the workout and then apply any adjustments that are to be
    # applied to the workout for the next time, so that the user sees exactly what
    # they will be doing in their next workout.
    use_last_instance = request.args.get('use_last_instance', 'false').lower() == 'true'

    # if use_last_instance:
    #     member_id = get_member_id_from_user_context(context)
    #     if not member_id:
    #         abort(401)
    #     last_instance = get_last_workout_instance_for_workout(workout['id'], member_id)
    #     if last_instance and last_instance.get('next_time_workout_sections', None):
    #         workout = last_instance
    #         workout[WORKOUT_SECTIONS] = workout['next_time_workout_sections']

    wrkout_exercises = get_exercises_from_workout(workout)
    exercises = { ex.get('id', None): ex for ex in wrkout_exercises }


    if not workout:
        abort(404)
    
    # Get current workout state to see if there are any parameter overrides
    current_workout_state = get_active_workout_state()
    current_parameters = {}
    if current_workout_state:
        current_parameters = current_workout_state.get('exercise_parameters', {})
    
    # new: only use the session value if it exists
    last = session.get(f"last_section_{workout_key_str}")  # no fallback
    if use_last_instance:
        workout_sections = workout['next_time_workout_sections'] if workout.get('next_time_workout_sections', None) else workout[WORKOUT_SECTIONS]
    else:
        workout_sections = workout[WORKOUT_SECTIONS]        
    # if last section is not set, then we set the last section to be the first section of the workout that has more than one exercise in it
    if not last:
        for section in workout_sections:
            if len(section.get('exercises', [])) > 0:
                last = section.get('name', None)
                break
        
    return render_template(
        "popup_workout_view.html",
        workout=workout,
        workout_sections=workout_sections,
        exercises=exercises,
        current_parameters=current_parameters,
        workout_definition_key=workout_key_str,
        default_section=last,
        show_finish_button=False,
        rs=rm_spaces,
        is_modal=is_modal
    )

from common.fitness.entities_getter import get_entity

# @bp.route("/viewer/workout/<workout_id>/section/<section_name>")
# @auth.login_required
# def view_section(context=None, workout_id=None, section_name=None):
#     workout = get_entity(WORKOUT_ENTITY_NAME, workout_id)
#     exercises = get_exercises_from_workout(workout)
#     if not workout:
#         abort(404)
#     section = next((s for s in workout[WORKOUT_SECTIONS] if s["name"] == section_name), None)
#     if not section:
#         abort(404)
#     print(f"Viewing section {section_name} of workout {workout_id}")    
#     # Get current workout state to see if there are any parameter overrides
#     current_workout_state = get_active_workout_state()
#     current_parameters = {}
#     if current_workout_state:
#         current_parameters = current_workout_state.get('exercise_parameters', {})
    
#     # Persist the user's current section in session
#     session[f"last_section_{workout_id}"] = section_name
#     return render_template("_section_view.html",
#                            section=section,
#                            workout=workout,
#                            exercises=exercises,
#                            current_parameters=current_parameters)

@bp.route("/viewer/workout/<workout_id>/set_section/<section_name>", methods=["POST"])
@auth.login_required
def set_last_section(context=None, workout_id=None, section_name=None):
    # guard: make sure section_name is valid for this workout_id…
    print(f"Setting last section for workout {workout_id} to {section_name}")
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

    current_workout_state = get_active_workout_state()
    current_app.logger.info(f"Current workout state: {current_workout_state}")

    adjustments = current_workout_state.get('adjustments', {})
    exercise_adjustment = adjustments.get(exercise_id, 0)
    if adjust == 'up':
        exercise_adjustment += 5
    elif adjust == 'down':
        exercise_adjustment -= 5
    adjustments[exercise_id] = exercise_adjustment
    current_workout_state['adjustments'] = adjustments
    update_active_workout_state(current_workout_state)

    adjust_str = format_exercise_adjustment(exercise_adjustment)

    return f'<p id="adjust-{exercise_id}-{workout_id}" hx-swap-oob="true" style="text-align: right;">{adjust_str}</p>'

# this route is used to display the details of workouts that have been completed
# it is used in the workout history page, and it displays the details of a workout, including date & time of the workout, 
# the exercises performed, and the parameters used for each exercise
@bp.route('/view_workout_detail')
@auth.login_required
def view_workout_detail(context):
    es = EntityStore()
    workout_key_str = request.args.get("workout_key", None)
    workout_key = eval(workout_key_str) if workout_key_str else None
    workout = es.get_item_by_composite_key(workout_key)
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

def format_exercise_adjustment(exercise_adjustment=None):
    adjust_str = ''
    try:
        if exercise_adjustment is None:
            return ''
        # if int(exercise_adjustment) > 0:
        #     adjust_str = f'next workout: +{exercise_adjustment}'
        # elif int(exercise_adjustment) < 0:
        #     adjust_str = f'next workout: - {abs(exercise_adjustment)}'
        # else:
        #     adjust_str = ''
    except Exception as e:
        adjust_str = ''
    return adjust_str

bp.add_app_template_filter(format_exercise_adjustment, name='format_adjustment')



@bp.route("/viewer/exercise/edit_params")
@auth.login_required
def edit_exercise_parameters(context=None):
    """Display the parameter edit dialog for an exercise in the current workout"""
    current_app.logger.info(f"=== EDIT PARAMS ROUTE CALLED ===")
    exercise_id = request.args.get("exercise_id", None)
    workout_id = request.args.get("workout_id", None)
    workout_instance_key = request.args.get("workout_instance_key", None)
    current_app.logger.info(f"exercise_id from args: {exercise_id}")
    current_app.logger.info(f"workout_id from args: {workout_id}")
    current_app.logger.info(f"workout_instance_key from args: {workout_instance_key}")
    current_app.logger.info(f"request.args: {request.args}")
    current_app.logger.info(f"request.url: {request.url}")
    
    if not exercise_id:
        abort(400, "exercise_id is required")
    if not workout_instance_key:
        abort(400, "workout_key is required")
    
    # Get the exercise details
    exercise = get_entity("ExerciseTable", exercise_id)
    current_app.logger.info(f"exercise found: {exercise is not None}")
    if not exercise:
        abort(404)
    es = EntityStore()
    # Get the workout details to find the exercise parameters
    workout_instance = es.get_item_by_composite_key(workout_instance_key)
    workout = get_entity(WORKOUT_ENTITY_NAME, workout_id)
    if not workout_instance:
        abort(404)
    
    # Find the exercise item in the workout to get original parameters
    item = None
    current_app.logger.info(f"Looking for exercise_id '{exercise_id}' in workout sections...")
    current_app.logger.info(f"Workout sections: {[s.get('name') for s in workout_instance.get(WORKOUT_SECTIONS, [])]}")
    
    for section in workout_instance.get(WORKOUT_SECTIONS, []):
        section_name = section.get("name", "unknown")
        current_app.logger.info(f"Checking section '{section_name}' with {len(section.get('exercises', []))} exercises")
        for ex_item in section.get("exercises", []):
            ex_item_id = ex_item.get("id")
            current_app.logger.info(f"  Comparing '{ex_item_id}' with '{exercise_id}' - match: {ex_item_id == exercise_id}")
            if ex_item_id == exercise_id:
                item = ex_item
                current_app.logger.info(f"Found exercise in section '{section_name}'!")
                break
        if item:
            break
    
    if not item:
        current_app.logger.error(f"Exercise '{exercise_id}' not found in any workout section!")
        current_app.logger.error(f"Available exercise IDs in workout: {[ex.get('id') for section in workout.get(WORKOUT_SECTIONS, []) for ex in section.get('exercises', [])]}")
        abort(404, "Exercise not found in workout")
    
    # Get current workout state to see if there are any parameter overrides
    current_workout_state = get_active_workout_state()
    current_parameters = get_initial_params_for_exercise()
    p = item.get('parameters', {})
    current_parameters.update(p)

    if current_workout_state:
        exercise_parameters = current_workout_state.get('exercise_parameters', {})
        p = exercise_parameters.get(exercise_id, {})
        if p:
            current_parameters.update(p)
    
    return render_template("_exercise_parameters_edit.html",
                           exercise=exercise,
                           workout=workout_instance,
                           workout_id=workout_id,
                           workout_instance_key=workout_instance_key,
                           item=item,
                           current_parameters=current_parameters)

@bp.route("/viewer/exercise/save_params", methods=["POST"])
@auth.login_required
def save_exercise_parameters(context=None):
    """Save updated exercise parameters for the current workout"""
    exercise_id = request.args.get("exercise_id", None)
    workout_id = request.args.get("workout_id", None)
    workout_instance_key = request.args.get("workout_instance_key", None)
    if not exercise_id:
        abort(400, "exercise_id is required")
    if not workout_id:
        abort(400, "workout_id is required")
    
    # Get the exercise details
    exercise = get_entity("ExerciseTable", exercise_id)
    if not exercise:
        abort(404)
    
    es = EntityStore()
    # Get the workout details to find the exercise parameters
    workout_instance = es.get_item_by_composite_key(workout_instance_key)
    if not workout_instance :
        abort(404)
    
    # Find the exercise item in the workout to get original parameters
    item = None
    for section in workout_instance.get(WORKOUT_SECTIONS, []):
        for ex_item in section.get("exercises", []):
            if ex_item.get("id") == exercise_id:
                item = ex_item
                break
        if item:
            break
    
    if not item:
        abort(404, "Exercise not found in workout")
    
    # Get form data for new parameters
    new_parameters = {}
    if request.form.get("sets"):
        new_parameters["sets"] = int(request.form.get("sets"))
    if request.form.get("reps"):
        new_parameters["reps"] = int(request.form.get("reps"))
    if request.form.get("weight"):
        new_parameters["weight"] = float(request.form.get("weight"))
    if request.form.get("weight_unit"):
        new_parameters["weight_unit"] = request.form.get("weight_unit")
    if request.form.get("time"):
        new_parameters["time"] = int(request.form.get("time"))
    
    current_app.logger.info(f"Saving exercise parameters for {exercise_id}: {new_parameters}")
    
    # Update workout state with new parameters
    current_workout_state = get_active_workout_state()
    if not current_workout_state:
        current_workout_state = {}
    
    exercise_parameters = current_workout_state.get('exercise_parameters', {})
    exercise_parameters[exercise_id] = new_parameters
    current_workout_state['exercise_parameters'] = exercise_parameters
    update_active_workout_state(current_workout_state)
    
    # Return updated parameter display HTML
    return render_template("_exercise_parameters_display.html",
                           exercise_id=exercise_id,
                           workout_id=workout_id,
                           workout_instance_key=workout_instance_key,
                           item=item,
                           current_parameters=new_parameters)


@bp.route("/viewer/exercise/save_future_params", methods=["POST"])
@auth.login_required
def save_future_exercise_parameters(context=None):
    """Save updated default parameters for future workouts with this exercise"""
    exercise_id = request.args.get("exercise_id", None)
    workout_id = request.args.get("workout_id", None)
    workout_instance_key = request.args.get("workout_instance_key", None)

    if not exercise_id:
        abort(400, "exercise_id is required")
    if not workout_id:
        abort(400, "workout_id is required")
    
    # Get the exercise details
    exercise = get_entity("ExerciseTable", exercise_id) 
    if not exercise:
        abort(404)

    es = EntityStore()
    # Get the workout details to find the exercise parameters
    workout_instance = es.get_item_by_composite_key(workout_instance_key)
    if not workout_instance :
        abort(404)

    # Find the exercise item in the workout to get original parameters
    item = None
    for section in workout_instance.get(WORKOUT_SECTIONS, []):
        for ex_item in section.get("exercises", []):
            if ex_item.get("id") == exercise_id:
                item = ex_item
                break
        if item:
            break
    
    if not item:
        abort(404, "Exercise not found in workout")


    
    # Get form data for new default parameters
    new_parameters = {}
    if request.form.get("sets"):
        new_parameters["sets"] = int(request.form.get("sets"))
    if request.form.get("reps"):
        new_parameters["reps"] = int(request.form.get("reps"))
    if request.form.get("weight"):
        new_parameters["weight"] = float(request.form.get("weight"))
    if request.form.get("weight_unit"):
        new_parameters["weight_unit"] = request.form.get("weight_unit")
    if request.form.get("time"):
        new_parameters["time"] = int(request.form.get("time"))
    
    current_app.logger.info(f"Saving future exercise parameters for {exercise_id}: {new_parameters}")
    
    # Update workout state with new parameters
    current_workout_state = get_active_workout_state()
    if not current_workout_state:
        current_workout_state = {}
    adjustments = current_workout_state.get('adjustments', {})
    adjustments[exercise_id] = new_parameters
    current_workout_state['adjustments'] = adjustments
    update_active_workout_state(current_workout_state)


    return render_template("_exercise_parameters_nexttime_display.html",
                           exercise_id=exercise_id,
                           workout_id=workout_id,
                           workout_instance_key=workout_instance_key,
                           item=item,
                           current_parameters=new_parameters)


@bp.route("/viewer/exercise/search", methods=["POST"])
@auth.login_required
def search_exercises(context=None):
    """Search for exercises to replace current exercise"""
    search_term = request.form.get("exercise-search", "").strip()
    category = request.form.get("search-category", "")
    
    # Get current context parameters from URL args or form
    exercise_id = request.args.get("exercise_id") or request.form.get("exercise_id")
    workout_id = request.args.get("workout_id") or request.form.get("workout_id") 
    workout_instance_key = request.args.get("workout_instance_key") or request.form.get("workout_instance_key")
    
    # Use the member ID from context for filtering
    member_id = get_member_id_from_user_context(context)
    if not member_id:
        abort(401)
    
    # Get all exercises first
    fields_to_display = get_fitnessclub_listing_fields_for_entity("ExerciseTable")
    all_exercises = get_entities("ExerciseTable", fields_to_display)
    
    # Filter exercises in-memory
    filtered_exercises = []
    for exercise in all_exercises:
        # Search filter
        if search_term and search_term.lower() not in exercise.name.lower():
            continue
        
        # Category filter
        if category and exercise.category != category:
            continue
            
        filtered_exercises.append(exercise)
    
    # Limit results
    filtered_exercises = filtered_exercises[:20]
    
    if not filtered_exercises:
        return '<p class="text-muted text-center">No exercises found.</p>'
    
    return render_template("_exercise_search_results.html", 
                         exercises=filtered_exercises,
                         exercise_id=exercise_id,
                         workout_id=workout_id,
                         workout_instance_key=workout_instance_key)


@bp.route("/viewer/exercise/replace", methods=["POST"])
@auth.login_required
def replace_exercise(context=None):
    """Replace current exercise in workout"""
    current_exercise_id = request.args.get("current_exercise_id", None)
    new_exercise_id = request.args.get("new_exercise_id", None)
    workout_instance_key = request.args.get("workout_instance_key", None)
    workout_id = request.args.get("workout_id", None)
    
    if not all([current_exercise_id, new_exercise_id, workout_instance_key]):
        abort(400, "Missing required parameters")
    
    # Get the new exercise details
    new_exercise = get_entity("ExerciseTable", new_exercise_id)
    if not new_exercise:
        abort(404, "New exercise not found")
    
    es = EntityStore() 
    
    # Get the workout instance
    workout_instance = es.get_item_by_composite_key(workout_instance_key)
    if not workout_instance:
        abort(404, "Workout instance not found")
    
    # Find and replace the exercise in the workout
    updated = False
    for section in workout_instance.get(WORKOUT_SECTIONS, []):
        for i, ex_item in enumerate(section.get("exercises", [])):
            if ex_item.get("id") == current_exercise_id:
                # Keep the same parameters but change the exercise
                section["exercises"][i]["id"] = new_exercise_id
                section["exercises"][i]["name"] = new_exercise.name
                updated = True
                break
        if updated:
            break
    
    if updated:
        es.store_entity(workout_instance)
        
        # Update workout state to track the replacement
        current_workout_state = get_active_workout_state()
        if not current_workout_state:
            current_workout_state = {}
        
        exercise_replacements = current_workout_state.get('exercise_replacements', {})
        exercise_replacements[current_exercise_id] = {
            'original_exercise_id': current_exercise_id,
            'new_exercise_id': new_exercise_id,
            'new_exercise_name': new_exercise.name,
            'replaced_at': datetime.utcnow().isoformat()
        }
        current_workout_state['exercise_replacements'] = exercise_replacements
        update_active_workout_state(current_workout_state)
        
        return f'<div class="alert alert-success">Exercise replaced successfully! Now using: {new_exercise.name}</div>'
    else:
        return '<div class="alert alert-danger">Failed to replace exercise.</div>'
    


@bp.route("/get-editor-for-parameter/<workout_id>/<exercise_id>/<param>")
def get_edit_form(workout_id, exercise_id, param, context=None):
    orig_param_value = request.args.get("value", "")
    unit_param_value = request.args.get("unit-param-value", "")
    active_workout = request.args.get("active_workout", "false").lower() == "true"
    purpose_of_parameter_edit = request.args.get('purpose_of_parameter_edit', None)
    component_id = f"param-{workout_id}-{exercise_id}-{param}"
    # this is where we would look at the exercise definition to determine the type of the parameter and return the appropriate editor. 
    # which for now is just return a text input for all parameters.
    # the types of editors we want to support include:
    # - numeric input for parameters like "R", "S", and "F", when "Fu" is kg or lbs.  
    # - if Fu is "bands", then F 
    #   becomes a dropdown with options like "light (yellow)", "medium (green)", "heavy (black)". 
    #   So we would need to look at the current values of the parameter unit to determine the type of editor to return.
    # - dropdown for parameters for standard units,
    #   e.g Fu force units - [kg, lbs], or for Tu time units - (sec, min, hour), Du distance units - (meters, yards, miles) and Pu - pace units (rate, tempo)
    # - text input 
    # 
    # seems like the exercise object would hold the relationship between parameter units and the domain of values for that parameter
    # e.g. if Fu is kg or lb, then F would be numeric, perhaps with a certain range of valid values. If Fu is bands, then F would be a dropdown 
    # with options like light, medium, heavy. So we would need to look at the current value of Fu to determine the type of editor to return for F.
    # so the logic would be:
    # 1) get the current value of the parameter that we want to edit (which is passed in as a query parameter for now, but could also be looked up from the workout definition or workout instance)
    # 2) determine the type of the parameter (numeric, dropdown, text) based on the current value and the exercise definition
    # 3) return the appropriate editor for that parameter type, with the current value pre-filled in the editor.
    #
    # I think we need 2 functions to determine the range of values for a parameter (both funcs would take the exercise definition as input):
    # 1) a function that accepts a unit parameter, Fu, Tu, Du, or Pu, and returns the range of values for that unit, e.g Fu is ["kg", "lbs"], Tu is ["sec", "min", "hour"], Du is ["meters", "yards", "miles"], Pu is ["rate", "tempo"]
    # 2) a funtion that accepts the parameter we want to edit, e.g. F, T, D, or P, and the current value of the unit parameter, e.g. Fu, Tu, Du, or Pu, and 
    # returns the appropriate editor type and range of values for that parameter.
    # so the editor for a F parameter would be numeric if Fu is kg or lbs, but would be a dropdown with options light, medium, heavy if Fu is bands.
    #

    if param in ['Fu', 'Tu', 'Du', 'Pu']:
        editor_info = get_editor_type_for_unit_parameter(param, None)
    else:
        editor_info = get_editor_type_for_value_parameter(param, unit_param_value, None)

    if editor_info['type'] == 'choice':
        options_html = "".join([f'<option value="{opt}" {"selected" if opt == orig_param_value else ""}>{opt}</option>' for opt in editor_info['options']])
        return f"""
            <form id="{component_id}" 
                hx-put="/workouts/update-workout-param-value/{workout_id}/{exercise_id}/{param}?purpose_of_parameter_edit={purpose_of_parameter_edit}" 
                hx-target="#{component_id}" 
                hx-swap="outerHTML" 
                class="d-inline-block flex-shrink-0"
                hx-trigger="change, focusout">
                <input type="hidden" name="orig_param_value" value="{orig_param_value}">
                <input type="hidden" name="active_workout" value="{active_workout}">
                <input type="hidden" name="unit_param_value" value="{unit_param_value}">
                <select
                    name="new-param-value"
                    class="form-select form-select-sm"
                    size="3"
                    style="width: 7rem; min-width: 7rem; color: #212529; background-color: #fff; flex: 0 0 auto;"
                    autofocus >
                    {options_html}
                </select>                
            </form>
        """
    else:
        input_type = "number" if editor_info['type'] == 'numeric' else "text"
        return f"""
                <!-- The editable form (returned by server) -->
                <form id="{component_id}" 
                    hx-put="/workouts/update-workout-param-value/{workout_id}/{exercise_id}/{param}?purpose_of_parameter_edit={purpose_of_parameter_edit}" 
                    hx-target="#{component_id}" 
                    hx-swap="outerHTML" 
                    hx-trigger="focusout">
                    <input type="hidden" name="orig_param_value" value="{orig_param_value}">
                    <input type="hidden" name="active_workout" value="{active_workout}">
                    <input type="hidden" name="unit_param_value" value="{unit_param_value}">                
                    <input type="{input_type}" 
                        name="new-param-value" 
                        value="{orig_param_value}" 
                        style="width: 6ch; max-width: 8ch;"
                        onfocus="this.select()"
                        onkeydown="if (event.key === 'Enter') {{ event.preventDefault(); this.blur(); }}"
                        autofocus>
                </form>
                """

def get_initial_editable_text2(workout_id, exercise_id, param, param_value, active_workout="false", purpose_of_parameter_edit=None):
    # This function would typically fetch the current text from a database based on the item_id
    component_id = f"param-{workout_id}-{exercise_id}-{param}"
    unit_param_component_id = f"param-{workout_id}-{exercise_id}-{param}u"
    is_a_unit_param = True if len(param) == 2 and param[1] == 'u' else False

    if is_a_unit_param:
        unit_param_htmx = 'name="unit-param-value"'
    else:
        unit_param_htmx = f"""
        hx-vals='js:{{ "unit-param-value": document.getElementById("{unit_param_component_id}")?.textContent.trim() || "" }}' 
        name="{param}"
        """

    new_html =  f"""
                <div id="{component_id}"
                  class="d-flex align-items-baseline"
                  hx-get="/workouts/get-editor-for-parameter/{workout_id}/{exercise_id}/{param}?value={param_value}&active_workout={active_workout}&purpose_of_parameter_edit={purpose_of_parameter_edit}"
                  {unit_param_htmx}
                  hx-target="#{component_id}" 
                  hx-trigger="click"
                  hx-swap="outerHTML">
                  { param_value }
                  <i class="bi bi-pencil-square text-muted ms-1" style="font-size: 0.75rem; margin-left:0px;" title="Click to edit"
                    aria-hidden="true"></i>
                </div>           
           """

    # old_html = f"""
    #   <div id="{component_id}"
    #    class="d-flex align-items-baseline"
	#    hx-get="/workouts/get-editor-for-parameter/{workout_id}/{exercise_id}/{param}?value={param_value}"
	#    hx-target="#{component_id}"
	#    hx-trigger="click"
	#    hx-swap="outerHTML">
	#    { param_value }
    #    <i class="bi bi-pencil-square text-muted ms-1" style="font-size: 0.75rem; margin-left:0px;" title="Click to edit"
    #           aria-hidden="true"></i>
	#   </div>
    # """   

    return new_html

