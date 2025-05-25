from flask import Blueprint, redirect, render_template, request, url_for
from common.fitness.active_fitness_registry import get_fitnessclub_entity_filters_for_entity, get_fitnessclub_filter_func_for_entity, get_fitnessclub_filter_term_for_entity
from common.fitness.entities_getter import get_filtered_entities
from common.fitness.hx_common import hx_render_template
bp = Blueprint('program', __name__, template_folder='templates')
from auth import auth

# @bp.route('/')
# @auth.login_required
# def root(context=None):
#     return hx_render_template('program.html', context=context)

@bp.route('/')
@auth.login_required
def index(context=None):
    return redirect(url_for('program.workouts_listing'), 302)

@bp.route('/workouts-listing')
@auth.login_required
def workouts_listing(context=None):
    WORKOUT_ENTITY_NAME = "WorkoutTable"
    page = int(request.args.get('page', 1))
    page_size = 10

    fields_to_display  = ['name']
    filters = get_fitnessclub_entity_filters_for_entity(WORKOUT_ENTITY_NAME)

    if filters:
        filter_func  = get_fitnessclub_filter_func_for_entity(WORKOUT_ENTITY_NAME)
        filter_term_func  = get_fitnessclub_filter_term_for_entity(WORKOUT_ENTITY_NAME)
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
    return render_template(
        "entity_list_component.html",
        entity_name=WORKOUT_ENTITY_NAME,
        main_content_container="entities-container",        
        fields_to_display=fields_to_display,
        entities=current,
        filter_terms=filter_terms,
        args=request.args,
        page=page,
        total_pages=total_pages,
        entities_listing_route=f'/program/workouts-listing?entity_table={WORKOUT_ENTITY_NAME}',
        entity_action_route=f'/workouts/viewer/workout?entity_table={WORKOUT_ENTITY_NAME}',
        entity_action_icon='bi-pencil-square',         
        context=context)
