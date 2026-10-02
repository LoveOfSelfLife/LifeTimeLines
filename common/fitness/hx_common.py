from ast import pattern

from common.template_renderer import hx_render_template
from common.member_entity import get_member_id_from_user_context
from common.fitness.roles_service import get_member_role_context

def hx_render_fitness_template(template_file=None, template_string=None, **kwargs):
    context = kwargs.get('context', None)
    if context:
        member_id = get_member_id_from_user_context(context)
        role_context = get_member_role_context(member_id)
        kwargs['member_id'] = member_id
        kwargs['role_context'] = role_context
    return hx_render_template(template_file=template_file, template_string=template_string, **kwargs)



