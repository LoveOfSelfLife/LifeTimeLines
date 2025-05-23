from flask import Blueprint, redirect, render_template, request, url_for
from common.entity_store import EntityStore
from common.fitness.active_fitness_registry import get_fitnessclub_entity_filters_for_entity, get_fitnessclub_entity_type_for_entity, get_fitnessclub_filter_func_for_entity, get_fitnessclub_filter_term_for_entity, get_fitnessclub_listing_fields_for_entity, render_exercise_popup_viewer_html
from common.fitness.entities_getter import get_filtered_entities
from common.fitness.hx_common import hx_render_template
bp = Blueprint('exercises', __name__, template_folder='templates')
from auth import auth

@bp.route('/')
@auth.login_required
def root(context=None):
    return redirect(url_for('exercises.exercises_fragment'), 302)

@bp.route('/exercises-listing')
@auth.login_required
def exercises_fragment(context=None):
    entity_name = "ExerciseTable"
    page = int(request.args.get('page', 1))

    page_size = 10

    fields_to_display  = ['name']
    filters = get_fitnessclub_entity_filters_for_entity(entity_name)

    if filters:
        filter_func  = get_fitnessclub_filter_func_for_entity(entity_name)
        filter_term_func  = get_fitnessclub_filter_term_for_entity(entity_name)
        filter_terms = filter_term_func(request.args)
    else:
        filter_func = None
        filter_terms = None

    entities = get_filtered_entities(entity_name, fields_to_display, filter_func, filter_terms)

    total_pages = (len(entities) + page_size - 1) // page_size
    start = (page - 1) * page_size
    end = start + page_size
    current = entities[start:end]

    return render_template(
        "entity_list_component.html",
        entity_name=entity_name,
        main_content_container="entities-container",        
        fields_to_display=fields_to_display,
        entities=current,
        filter_terms=filter_terms,
        args=request.args,
        page=page,
        total_pages=total_pages,
        filter_dialog_route=f'/exercises/filter-dialog?entity_table={entity_name}',        
        entities_listing_route=f'/exercises/exercises-listing?entity_table={entity_name}',
        entity_view_route=f'/exercises/view?entity_table={entity_name}',
        # entity_action_route=f'/admin/edit?entity_table={entity_name}',
        # entity_action_icon='bi-pencil-square'
    )


@bp.route('/modal')
@auth.login_required
def show_modal(context=None):
    return render_template('modal-here.html', context=context)

@bp.route('/view')
@auth.login_required
def view_exercise_details(context=None):
    table_id = "ExerciseTable"
    entity_instance = get_fitnessclub_entity_type_for_entity(table_id)

    composite_key_str = request.args.get('key', None)
    composite_key = eval(composite_key_str) if composite_key_str else None
    es = EntityStore()
    entity_to_view = es.get_item_by_composite_key(entity_instance, composite_key)
    
    return render_exercise_popup_viewer_html(context, entity_to_view)

@bp.route('/filter-dialog')
@auth.login_required
def filter_dialog(context=None):
    entity_name = "ExerciseTable"
    entity_type = get_fitnessclub_entity_type_for_entity(entity_name)
    filters = get_fitnessclub_entity_filters_for_entity(entity_name)

    return hx_render_template('filter_dialog.html', 
                              entities_listing_route=f'/exercises/exercises-listing?entity_table={entity_name}',
                              entity_display_name=entity_type.get_display_name(),                              
                              entity_name=entity_name,
                              filters=filters,
                              args=request.args,
                              context=context)

