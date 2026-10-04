from common.member_entity import FirstTimeUserException, MembershipRegistry, UnregisteredMemberException, get_member_email_from_user_context, get_member_id_from_user_context, get_member_name_from_user_context, is_member_an_admin
from common.app_info import get_current_app_metadata
from common.impersonation import get_impersonated_member_id
from flask import abort, render_template, render_template_string, request
from common.roles_service import get_member_role_context


def hx_render_template(template_file=None, template_string=None, **kwargs):
    context = kwargs.get('context', None)
    if context:
        member_id = get_member_id_from_user_context(context)
        role_context = get_member_role_context(member_id)
        kwargs['member_id'] = member_id
        kwargs['role_context'] = role_context    
    if request.headers.get("HX-Request"):
        return _render_template_string_or_file(template_file, template_string, **kwargs)
    else:
        members_registry = MembershipRegistry()
        if context:
            member_id = kwargs.get('member_id', None)
            try:
                member = members_registry.verify_member_registration(member_id)
                kwargs['member'] = member
                content = _render_template_string_or_file(template_file, template_string, **kwargs)
                show_admin_menu = is_member_an_admin(member_id)
                impersonated_member_id = get_impersonated_member_id()
                impersonated_member = None
                if impersonated_member_id:
                    impersonated_member = members_registry.get_member(impersonated_member_id)

                return render_template('app.html', app_metadata=get_current_app_metadata(),
                                     content=content, show_admin_menu=show_admin_menu,
                                    impersonated_member=impersonated_member, **kwargs)

            except UnregisteredMemberException as e:
                print(f"User not registered exception: {e}")
                member = members_registry.get_member(member_id)
                kwargs['member'] = member
                return render_template("unregistered_member.html", 
                                       **kwargs)

            except FirstTimeUserException as e:
                print(f"First time user exception: {e}")
                member_email = get_member_email_from_user_context(context)
                member_name = get_member_name_from_user_context(context)
                members_registry.add_member(member_id, member_email, member_name)
                member = members_registry.get_member(member_id)
                kwargs['member'] = member
                return render_template("first_time_user.html", 
                                       **kwargs)
        else:
            abort(401)

def _render_template_string_or_file(template_file=None, template_string=None, **kwargs):
    """
    Renders a template from a file or a string based on whether the request has a file or a string.
    """
    if template_string:
        return render_template_string(template_string, **kwargs)
    else:
        return render_template(template_file, **kwargs)

def rm_spaces(s):
    return s.replace(' ', '_').lower() if s else s


