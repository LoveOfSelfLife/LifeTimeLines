from ast import literal_eval
import json
from urllib import response
from flask import Blueprint, abort, make_response, redirect, render_template, request, session, url_for, jsonify
from common.entity_store import EntityStore
from common.fitness.active_fitness_registry import get_fitnessclub_entity_filters_for_entity, get_entity_obj_from_entity_name, get_fitnessclub_listing_fields_for_entity
from common.fitness.entities_getter import resolve_selected_entity_keys
from common.fitness.entities_getter import as_bool
from common.fitness.entities_getter import MULTI_SELECT_SESSION_KEY
from common.fitness.exercise_entity import show_exercise_viewer
from common.fitness.hx_common import parse_listing_filter
from common.fitness.entities_getter import get_entities
from common.fitness.exercise_entity import ExerciseEntity
from common.fitness.hx_common import get_filter_terms_from_request, hx_render_template
from common.fitness.member_entity import get_member_id_from_user_context
from common.fitness.exercise_schema import exercise_schema
from common.fitness.member_exercise_history import get_exercise_history_for_member
from common.fitness.utils import generate_id
bp = Blueprint('exercises', __name__, template_folder='templates')
from auth import auth
@bp.route('/')
@auth.login_required
def root(context=None):
    member_id = get_member_id_from_user_context(context)
    if not member_id:
        abort(401)
    page = int(request.args.get('page', 1))
    filter_terms = get_filter_terms_from_request()

    return exercises_listing2(member_id, page=page, filter_terms=filter_terms)

@bp.route('/exercises-listing', methods=['GET', 'POST'])
@auth.login_required
def exercises_listing(context=None):
    member_id = get_member_id_from_user_context(context)
    if not member_id:
        abort(401)
    page = int(request.args.get('page', 1))
    filter_terms = get_filter_terms_from_request()   
    # modal_mode = as_bool(request.args.get('modal_mode', None), False) if request.method == 'GET' else as_bool(request.form.get('modal_mode', None), False)     
    return exercises_listing2(member_id, page=page, filter_terms=filter_terms, modal_mode=False)


@bp.route('/listing-modal', methods=['GET'])
@auth.login_required
def exercises_listing_modal(context=None):
    member_id = get_member_id_from_user_context(context)
    if not member_id:
        abort(401)
    page = int(request.args.get('page', 1))
    filter_terms = get_filter_terms_from_request()
    if as_bool(request.args.get('allow_multi_select', None), False):
        session[MULTI_SELECT_SESSION_KEY] = []
    return exercises_listing2(member_id, page=page, filter_terms=filter_terms, modal_mode=True)

def exercises_listing2(member_id, page=1, filter_terms=[], modal_mode=False):
    entity_name = "ExerciseTable"

    page_size = 100

    # Handle view preference
    view = (request.form.get('view') if request.method == 'POST' 
            else request.args.get('view')) or session.get('view_preference', 'list')
    
    if view != session.get('view_preference'):
        session['view_preference'] = view
    
    fields_to_display = get_fitnessclub_listing_fields_for_entity(entity_name)
    
    entities = get_entities(entity_name, fields_to_display, filter_terms, member_id=member_id)

    allow_multi_select = as_bool(request.form.get('allow_multi_select', None),
                                  as_bool(request.args.get('allow_multi_select', None), False))
    selected_entity_keys = resolve_selected_entity_keys(allow_multi_select=allow_multi_select)

    # For checkbox toggles, avoid re-rendering listing content. Return only OOB state updates.
    if request.method == 'POST' and request.form.get('multi_select_toggle_key') is not None and allow_multi_select:
        multi_select_post_route = request.form.get('multi_select_post_route') or request.args.get('multi_select_post_route')
        preferred_section = request.form.get('preferred_section') or request.args.get('preferred_section')
        if multi_select_post_route and preferred_section and 'preferred_section=' not in multi_select_post_route:
            separator = '&' if '?' in multi_select_post_route else '?'
            multi_select_post_route = f"{multi_select_post_route}{separator}preferred_section={preferred_section}"

        return hx_render_template(
            'entity_multi_select_state_oob.html',
            allow_multi_select=allow_multi_select,
            selected_entity_keys=selected_entity_keys,
            multi_select_checkbox_name='selected_entity_keys',
            multi_select_post_route=multi_select_post_route,
            preferred_section=preferred_section,
        )

    return exercise_listing_base(
        entity_name,
        int(page),
        page_size,
        view,
        fields_to_display,
        filter_terms,
        entities,
        allow_multi_select=allow_multi_select,
        selected_entity_keys=selected_entity_keys,
        modal_mode=modal_mode,
    )


def exercise_listing_base(entity_name, page, page_size, view, fields_to_display, filter_terms, entities, allow_multi_select=False, selected_entity_keys=None, modal_mode=False):
    total_pages = (len(entities) + page_size - 1) // page_size
    start = (page - 1) * page_size
    end = start + page_size
    current = entities[start:end]
    selected_entity_keys = selected_entity_keys or []
    if request.headers.get('HX-Target') == 'results-area':
        template_file_name = 'entity_results_partial.html'
    else:
        template_file_name = 'entity_list_component.html'
    
    # Set results_target_container based on request args
    target = request.args.get('target')
    results_target_container = target if target else 'results-area'
    if modal_mode:
        entity_add_route = None
        entity_action_route=None
    else:
        entity_add_route = '/exercises/new?'
        entity_action_route='/exercises/edit?'

    multi_select_post_route = request.form.get('multi_select_post_route') or request.args.get('multi_select_post_route')
    multi_select_button_label = request.form.get('multi_select_button_label') or request.args.get('multi_select_button_label') or 'Add Selected'
    multi_select_button_icon = request.form.get('multi_select_button_icon') or request.args.get('multi_select_button_icon') or 'bi-plus-circle'
    preferred_section = request.form.get('preferred_section') or request.args.get('preferred_section')

    if multi_select_post_route and preferred_section and 'preferred_section=' not in multi_select_post_route:
        separator = '&' if '?' in multi_select_post_route else '?'
        multi_select_post_route = f"{multi_select_post_route}{separator}preferred_section={preferred_section}"

    entities_listing_route = f'/exercises/exercises-listing?entity_table={entity_name}'
    if allow_multi_select:
        entities_listing_route += '&allow_multi_select=true'

    template_data = dict(
        title="Exercises Library",
        entity_name=entity_name,
        main_content_container="entities-container",        
        fields_to_display=fields_to_display,
        entities=current,
        filter_terms=filter_terms,
        args=request.args,
        page=page,
        view=view,
        total_pages=total_pages,
        allow_multi_select=allow_multi_select,
        selected_entity_keys=selected_entity_keys,
        multi_select_checkbox_name='selected_entity_keys',
        multi_select_post_route=multi_select_post_route,
        multi_select_button_label=multi_select_button_label,
        multi_select_button_icon=multi_select_button_icon,
        preferred_section=preferred_section,
        entity_add_route=entity_add_route,
        filter_dialog_route=f'/exercises/filter-dialog?entity_table={entity_name}',        
        entities_listing_route=entities_listing_route,
        entity_view_route=f'/exercises/view?entity_table={entity_name}',
        entity_action_route=entity_action_route,
        entity_action_icon='bi-pencil-square',
        entity_action_label='Edit Exercise',
        favorite_toggle_route='/admin/toggle-favorite',
        results_target_container=results_target_container,
        entity_card_view_html='exercise_card_view.html'        
    )

    if modal_mode:
        return hx_render_template('exercise_listing_modal.html', **template_data)

    return hx_render_template(template_file_name, **template_data)


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

    return show_exercise_viewer(entity_to_view, context, show_dismiss_btn=True)

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
@bp.route('/exercise-history-dialog')
@auth.login_required
def exercise_history_dialog(context=None):
    entity_name = "ExerciseTable"
    entity_type = get_entity_obj_from_entity_name(entity_name)
    exercise_id = request.args.get('exercise_id', None)
    if not exercise_id:
        abort(400, "No exercise id provided")
    member_id = get_member_id_from_user_context(context)
    if not member_id:
        abort(401)
    ex_history = get_exercise_history_for_member(member_id, exercise_id)
    return hx_render_template('exercise_history_dialog.html', 
                              exercise_history=ex_history,
                              context=context)


# New Exercise Editor Routes

@bp.route('/new')
@auth.login_required
def new_exercise(context=None):
    """Create a new exercise using specialized editor"""
    # Initialize empty exercise with defaults from schema
    exercise_data = {}
    for field, props in exercise_schema['properties'].items():
        if 'default' in props:
            exercise_data[field] = props['default']
        else:
            # Handle array fields
            if props.get('type') == 'array':
                exercise_data[field] = []
            else:
                exercise_data[field] = ''

 
    return hx_render_template('exercises/exercise_editor.html',
                         exercise=exercise_data,
                         is_new=True,
                         schema=exercise_schema,
                         save_url='/exercises/save',
                         cancel_url=f'/exercises/cancel',
                         context=context)

@bp.route('/edit')
@auth.login_required
def edit_exercise(context=None):
    """Edit existing exercise using specialized editor"""
    # Get exercise by composite key (same pattern as view and admin)
    composite_key_str = request.args.get('key', None)
    if not composite_key_str:
        abort(400, "No exercise key provided")
        
    composite_key = eval(composite_key_str) if composite_key_str else None
    print(f"DEBUG: Retrieving exercise with composite key: {composite_key}")
    es = EntityStore()
    exercise_data = es.get_item_by_composite_key(composite_key)
    print(f"DEBUG: Raw exercise data retrieved: {exercise_data}")
    
    if not exercise_data:
        abort(404, "Exercise not found")
    
    # Remove Timestamp field if present
    if 'Timestamp' in exercise_data:
        del exercise_data['Timestamp']
    
    # here we need to determine if the current member can edit the exercise, which is the case if the member is an admin 
    # or if the exercise was created by the member
    member_id = get_member_id_from_user_context(context)
    can_edit = False
    if member_id:
        if exercise_data.get('created_by_member_id', None) == member_id:
            can_edit = True
        else:
            # check if the member is an admin
            from common.fitness.member_entity import is_member_an_admin
            if is_member_an_admin(member_id):
                can_edit = True
    if not can_edit:
        current_listing_page=request.args.get('page', 1)
        current_listing_filter_terms = get_filter_terms_from_request()
        response = make_response(exercises_listing2(member_id, page=current_listing_page, filter_terms=current_listing_filter_terms))
        response.headers['HX-Trigger'] = json.dumps({
            "showMessage": { "value": f"You do not have permission to edit this exercise.", "target": "body" }
        })

        return response
    # Parse images and videos fields if they are stored as strings (legacy data)
    for media_field in ['images', 'videos']:
        if media_field in exercise_data:
            media_value = exercise_data[media_field]
            print(f"DEBUG: Processing {media_field} - Type: {type(media_value)}, Value: {repr(media_value)}")
            if isinstance(media_value, str) and media_value.strip():
                try:
                    # Handle both single-quoted and double-quoted JSON strings
                    # Replace single quotes with double quotes for valid JSON
                    if media_value.startswith("[{'") or media_value.startswith("{'"):
                        media_value = media_value.replace("'", '"')
                    parsed_media = json.loads(media_value)
                    exercise_data[media_field] = parsed_media if isinstance(parsed_media, list) else []
                    print(f"SUCCESS: Parsed {media_field} from string: {len(parsed_media)} items - {parsed_media}")
                except (json.JSONDecodeError, ValueError) as e:
                    print(f"ERROR: Could not parse {media_field} field '{media_value}': {e}")
                    exercise_data[media_field] = []
            elif isinstance(media_value, list):
                # Already an array, keep as-is
                exercise_data[media_field] = media_value
                print(f"INFO: {media_field} is already an array: {len(media_value)} items - {media_value}")
            else:
                # Empty or invalid, set to empty array
                exercise_data[media_field] = []
                print(f"WARNING: {media_field} is empty or invalid type, setting to empty array")
        else:
            # Field doesn't exist, set to empty array
            exercise_data[media_field] = []
            print(f"INFO: {media_field} field doesn't exist, setting to empty array")

    # Parse primary and secondary muscles if they are strings
    for muscle_field in ['primaryMuscles', 'secondaryMuscles']:
        if muscle_field in exercise_data:
            muscle_value = exercise_data[muscle_field]
            if isinstance(muscle_value, str) and muscle_value.strip():
                try:
                    # Handle both single-quoted and double-quoted JSON strings
                    if muscle_value.startswith("[") or muscle_value.startswith("'"):
                        muscle_value = muscle_value.replace("'", '"')
                    parsed_muscles = json.loads(muscle_value)
                    exercise_data[muscle_field] = parsed_muscles if isinstance(parsed_muscles, list) else []
                except (json.JSONDecodeError, ValueError) as e:
                    print(f"Warning: Could not parse {muscle_field} field '{muscle_value}': {e}")
                    exercise_data[muscle_field] = []
            elif isinstance(muscle_value, list):
                exercise_data[muscle_field] = muscle_value
            else:
                exercise_data[muscle_field] = []
        else:
            exercise_data[muscle_field] = []
    
    print(f"Exercise data prepared - Images: {len(exercise_data.get('images', []))}, Videos: {len(exercise_data.get('videos', []))}")
    
    # Get exercise ID from the composite key or the data
    exercise_id = exercise_data.get('id')
    current_listing_page=request.args.get('page', 1)
    current_listing_filter=request.args.get('filter', '')   
    return hx_render_template('exercises/exercise_editor.html',
                         exercise=exercise_data,
                         is_new=False,
                         schema=exercise_schema,  
                         save_url=f'/exercises/save/{exercise_id}?page={current_listing_page}&filter={current_listing_filter}',
                         cancel_url=f'/exercises/cancel?page={current_listing_page}&filter={current_listing_filter}',
                         context=context)

@bp.route('/save', methods=['POST'])
@bp.route('/save/<exercise_id>', methods=['POST'])
@auth.login_required
def save_exercise(exercise_id=None, context=None):
    """Save exercise data from specialized editor"""
    try:
        # Get form data
        exercise_data = dict(request.form)
        print(f"DEBUG SAVE: Raw form data received: {dict(request.form)}")
        
        # Handle array fields (checkboxes and multi-selects)
        array_fields = ['primaryMuscles', 'secondaryMuscles', 'physical_fitness_components']
        for field in array_fields:
            if field in exercise_data:
                values = request.form.getlist(field)
                exercise_data[field] = values
            else:
                exercise_data[field] = []
        
        # Handle images and videos from media manager with safe JSON parsing
        images_data_raw = request.form.get('images_data', '[]').strip()
        print(f"DEBUG SAVE: Raw images_data received: {repr(images_data_raw)}")
        if images_data_raw:
            try:
                exercise_data['images'] = json.loads(images_data_raw)
                print(f"DEBUG SAVE: Parsed images data: {exercise_data['images']}")
            except (json.JSONDecodeError, ValueError) as e:
                print(f"ERROR SAVE: Invalid images_data JSON: {images_data_raw}, error: {e}")
                exercise_data['images'] = []
        else:
            exercise_data['images'] = []
            
        videos_data_raw = request.form.get('videos_data', '[]').strip()
        print(f"DEBUG SAVE: Raw videos_data received: {repr(videos_data_raw)}")
        if videos_data_raw:
            try:
                exercise_data['videos'] = json.loads(videos_data_raw)
                print(f"DEBUG SAVE: Parsed videos data: {exercise_data['videos']}")
            except (json.JSONDecodeError, ValueError) as e:
                print(f"ERROR SAVE: Invalid videos_data JSON: {videos_data_raw}, error: {e}")
                exercise_data['videos'] = []
        else:
            exercise_data['videos'] = []
            
        # Handle boolean fields
        exercise_data['hide'] = 'hide' in request.form
        
        # Generate ID for new exercise or use existing
        if exercise_id:
            exercise_data['id'] = exercise_id
        else:
            # Generate new ID based on exercise name
            exercise_name = exercise_data.get('name', '')
            exercise_data['id'] = generate_id(exercise_name)
            
        # Ensure required fields have defaults
        if 'origin' not in exercise_data or not exercise_data['origin']:
            exercise_data['origin'] = 'user-created'
        if 'type' not in exercise_data:
            exercise_data['type'] = ''
        if 'udf1' not in exercise_data:
            exercise_data['udf1'] = ''
        if 'udf2' not in exercise_data:
            exercise_data['udf2'] = ''
        
        exercise_data['created_by_member_id'] = get_member_id_from_user_context(context)

        print(f"Saving exercise data: {exercise_data}")
        
        # Create and save exercise entity
        exercise = ExerciseEntity(exercise_data)
        es = EntityStore()
        
        if exercise_id:
            # Update existing exercise
            es.upsert_item(exercise)
        else:
            # Create new exercise
            es.upsert_item(exercise)
        
        current_listing_page = int(request.args.get('page', 1))
        filter_param = request.args.get('filter', '')
        current_listing_filter = parse_listing_filter(filter_param)

        member_id = get_member_id_from_user_context(context)
        if not member_id:
            abort(401)
        response = make_response(exercises_listing2(member_id, page=current_listing_page, filter_terms=current_listing_filter))
        response.headers['HX-Trigger'] = json.dumps({
            "eventListChanged": { "target": "body" },
                "showMessage": { 
                "target": "body",
                "value": "exercise saved." }
            })
        return response
    
    except Exception as e:
        print(f"Error saving exercise: {str(e)}")
        import traceback
        traceback.print_exc()
        
        if request.headers.get('HX-Request'):
            return jsonify({"success": False, "error": str(e)}), 400
        else:
            abort(500, f"Error saving exercise: {str(e)}")

@bp.route('/cancel', methods=['POST'])
@auth.login_required
def cancel_exercise(exercise_id=None, context=None):
    """cancel editing exercise and redirect to listing"""

    member_id = get_member_id_from_user_context(context)
    if not member_id:
        abort(401)
    current_listing_page = int(request.args.get('page', 1))

    filter_param = request.args.get('filter', '')
    current_listing_filter = parse_listing_filter(filter_param)
        
    response = make_response(exercises_listing2(member_id, page=current_listing_page, filter_terms=current_listing_filter))
    response.headers['HX-Trigger'] = json.dumps({
        "eventListChanged": { "target": "body" },
            "showMessage": { 
            "target": "body",
            "value": "canceled." }
        })
    return response

