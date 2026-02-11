from ast import literal_eval
from flask import Blueprint, abort, redirect, render_template, request, session, url_for
from common.entity_store import EntityStore
from common.fitness.active_fitness_registry import _get_filter_terms_from_request, get_fitnessclub_entity_filters_for_entity, get_entity_obj_from_entity_name, get_fitnessclub_listing_fields_for_entity
from common.fitness.entities_getter import get_entities
from common.fitness.exercise_entity import render_exercise_popup_viewer_html
from common.fitness.hx_common import hx_render_template
from common.fitness.member_entity import get_member_detail_from_user_context
bp = Blueprint('exercises', __name__, template_folder='templates')
from auth import auth

@bp.route('/')
@auth.login_required
def root(context=None):
    return redirect(url_for('exercises.exercises_fragment'), 302)

@bp.route('/exercises-listing', methods=['GET', 'POST'])
@auth.login_required
def exercises_fragment(context=None):
    entity_name = "ExerciseTable"
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
    entities = get_entities(entity_name, fields_to_display, filter_terms, member_id=member_id)

    return exercise_listing_base(entity_name, page, page_size, view, fields_to_display, filter_terms, entities)


def exercise_listing_base(entity_name, page, page_size, view, fields_to_display, filter_terms, entities):
    total_pages = (len(entities) + page_size - 1) // page_size
    start = (page - 1) * page_size
    end = start + page_size
    current = entities[start:end]
    if request.headers.get('HX-Target') == 'results-area':
        template_file_name = 'entity_results_partial.html'
    else:
        template_file_name = 'entity_list_component.html'
    return render_template(
        template_file_name,
        entity_name=entity_name,
        main_content_container="entities-container",        
        fields_to_display=fields_to_display,
        entities=current,
        filter_terms=filter_terms,
        args=request.args,
        page=page,
        view=view,
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
    entity_instance = get_entity_obj_from_entity_name(table_id)

    composite_key_str = request.args.get('key', None)
    composite_key = eval(composite_key_str) if composite_key_str else None
    es = EntityStore()
    entity_to_view = es.get_item_by_composite_key(composite_key)
    
    return render_exercise_popup_viewer_html(context, entity_to_view)

@bp.route('/filter-dialog')
@auth.login_required
def filter_dialog(context=None):
    entity_name = "ExerciseTable"
    entity_type = get_entity_obj_from_entity_name(entity_name)
    filters = get_fitnessclub_entity_filters_for_entity(entity_name)
    view = request.args.get('view', 'list')
    return hx_render_template('filter_dialog.html', 
                              entities_listing_route=f'/exercises/exercises-listing?entity_table={entity_name}',
                              entity_display_name=entity_type.get_display_name(),                              
                              entity_name=entity_name,
                              filters=filters,
                              view=view,
                              args=request.args,
                              context=context)

