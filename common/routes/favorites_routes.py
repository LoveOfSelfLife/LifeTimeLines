
import datetime

from flask import json, render_template, request, abort
from common.blueprint import create_blueprint
from common.auth import auth
from common.entity_store import EntityStore, get_entity_obj_from_entity_name
from common.favorites_entity import toggle_entity_favorite
from common.member_entity import get_member_id_from_user_context, get_members_list
bp = create_blueprint('favorites', __name__)

@bp.route('/toggle', methods=['POST'])
@auth.login_required
def toggle_favorite(context=None):
    member_id = get_member_id_from_user_context(context)
    if not member_id:
        abort(401)

    entity_table = request.form.get('entity_table', None)
    entity_id = request.form.get('entity_id', None)

    if not entity_table or not entity_id:
        abort(400)

    entity = get_entity_obj_from_entity_name(entity_table)
    entity[entity.get_key_field()] = entity_id

    is_favorite = toggle_entity_favorite(entity, member_id)

    item_dom_id = request.form.get('item_dom_id', f'entity-item-{entity_id}')
    favorites_only = str(request.form.get('favorites_only', 'false')).lower() == 'true'

    html = render_template(
        'favorite_entity_toggle.html',
        favorite_entity_id=entity_id,
        favorite_entity_table=entity_table,
        favorite_item_dom_id=item_dom_id,
        favorite_is_active=is_favorite,
        favorite_toggle_route='/favorites/toggle',
        favorites_filter_active=favorites_only
    )

    if favorites_only and not is_favorite:
        dom_id_json = json.dumps(item_dom_id)
        html += f"\n<script>(function(){{const el=document.getElementById({dom_id_json});if(el){{el.remove();}}}})();</script>"

    return html
