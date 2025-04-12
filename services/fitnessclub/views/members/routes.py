from flask import Blueprint, render_template, request
from hx_common import hx_render_template, get_member_id
from common.fitness.member_info import get_members_list
bp = Blueprint('members', __name__, template_folder='templates')
from auth import auth

@bp.route('/')
@auth.login_required
def members(context=None):
    member_id = get_member_id(context)
    members_list = get_members_list()
    view_type='card'
    return hx_render_template('membership_list.html', members_list=members_list, current_member_id=member_id, view=view_type)
