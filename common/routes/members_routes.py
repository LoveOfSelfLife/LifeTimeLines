from flask import render_template, request
from common.blueprint import create_blueprint
from common.template_renderer import hx_render_template
from common.member_entity import get_member_id_from_user_context, get_members_list
bp = create_blueprint('members', __name__)
from common.auth import auth

@bp.route('/')
@auth.login_required
def members(context=None):
    member_id = get_member_id_from_user_context(context)
    members_list = get_members_list()
    view_type='card'
    return hx_render_template('membership_list.html', members_list=members_list, current_member_id=member_id, view=view_type)
