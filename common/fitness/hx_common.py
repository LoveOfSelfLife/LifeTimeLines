from flask import render_template, render_template_string, request
from common.fitness.member_entity import MembershipRegistry, get_member_email_from_user_context, get_member_id_from_user_context, get_member_name_from_user_context, is_member_an_admin, FirstTimeUserException, UnregisteredMemberException
from common.fitness.impersonation import get_impersonated_member_id
from common.fitness.roles_service import get_member_role_context

def rm_spaces(s):
    return s.replace(' ', '_').lower() if s else s

def render_template_string_or_file(template_file=None, template_string=None, **kwargs):
    """
    Renders a template from a file or a string based on whether the request has a file or a string.
    """
    if template_string:
        return render_template_string(template_string, **kwargs)
    else:
        return render_template(template_file, **kwargs)

def hx_render_template(template_file=None, template_string=None, **kwargs):
    context = kwargs.get('context', None)
    if request.headers.get("HX-Request"):
        return render_template_string_or_file(template_file, template_string, **kwargs)
    else:
        members_registry = MembershipRegistry()
        if context:
            member_id = get_member_id_from_user_context(context)
            try:
                member = members_registry.verify_member_registration(member_id)
                kwargs['member'] = member
                content = render_template_string_or_file(template_file, template_string, **kwargs)
                show_admin_menu = is_member_an_admin(member_id)
                
                # Add role-based context for menu rendering
                role_context = get_member_role_context(member_id)
                
                # Add impersonation information for display
                impersonated_member_id = get_impersonated_member_id()
                impersonated_member = None
                if impersonated_member_id:
                    impersonated_member = members_registry.get_member(impersonated_member_id)
                
                return render_template('base.html', content=content, show_admin_menu=show_admin_menu, 
                                     role_context=role_context, impersonated_member=impersonated_member, **kwargs)

            except UnregisteredMemberException as e:
                print(f"User not registered exception: {e}")
                member = members_registry.get_member(member_id)                
                kwargs['member'] = member
                # Unregistered members still have role info, provide context
                role_context = get_member_role_context(member_id)
                return render_template("unregistered_member.html", role_context=role_context, **kwargs)
            
            except FirstTimeUserException as e:
                print(f"First time user exception: {e}")
                member_email = get_member_email_from_user_context(context)
                member_name = get_member_name_from_user_context(context)
                members_registry.add_member(member_id, member_email, member_name)
                member = members_registry.get_member(member_id)
                kwargs['member'] = member
                # New members default to client role, so get basic role context
                role_context = get_member_role_context(member_id)
                return render_template("first_time_user.html", role_context=role_context, **kwargs)
        else:
            content = render_template_string_or_file(template_file, template_string, **kwargs)
            # we really should not ever get here, but just in case
            member={"user": "unknown", "admin": False}
            kwargs['member'] = member
            show_admin_menu = False
            impersonated_member = None
            # Default role context for unknown user
            role_context = {
                'member_id': None,
                'role': 'client',
                'is_admin': False,
                'current_team': None,
                'available_teams': [],
                'can_select_team': False
            }
            return render_template('base.html', content=content, show_admin_menu=show_admin_menu, 
                                 role_context=role_context, impersonated_member=impersonated_member, **kwargs)
        