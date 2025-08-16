from flask import render_template, render_template_string, request
from common.fitness.member_entity import MembershipRegistry, get_member_detail_from_user_context

class FirstTimeUserException(Exception):
    def __init__(self):
        super().__init__("First time user")

def rm_spaces(s):
    return s.replace(' ', '_').lower() if s else s

class UnregisteredMemberException(Exception):
    def __init__(self):
        super().__init__("Unregistered member")

def verify_member_registration(user):
    members_registry = MembershipRegistry()
    if not members_registry.check_if_member(user['id']):
        raise FirstTimeUserException()
    member = members_registry.get_member(user['id'])
    if member.get('level', 0) == 0:
        raise UnregisteredMemberException()
    member['admin'] = is_admin_member(user)
    return member

def is_admin_member(user):
    members_registry = MembershipRegistry()
    member = members_registry.get_member(user['id'])
    return member.get('level') >= 10

def render_template_string_or_file(template_file=None, template_string=None, **kwargs):
    """
    Renders a template from a file or a string based on whether the request has a file or a string.
    """
    if template_string:
        return render_template_string(template_string, **kwargs)
    else:
        return render_template(template_file, **kwargs)

def hx_render_template(template_file=None, template_string=None, **kwargs):

    if request.headers.get("HX-Request"):
        return render_template_string_or_file(template_file, template_string, **kwargs)
    else:
        if kwargs.get('context', None) is not None:
            user = get_member_detail_from_user_context(kwargs.get('context', None))
            try:
                member = verify_member_registration(user)
                kwargs['member'] = member
                content = render_template_string_or_file(template_file, template_string, **kwargs)
                return render_template('base.html', content=content, **kwargs)

            except UnregisteredMemberException as e:
                print(f"User not registered exception: {e}")
                members_registry = MembershipRegistry()
                member = members_registry.get_member(user['id'])                
                kwargs['member'] = member
                return render_template("unregistered_member.html", **kwargs)
            
            except FirstTimeUserException as e:
                print(f"First time user exception: {e}")
                members_registry = MembershipRegistry()
                members_registry.add_member(user)
                member = members_registry.get_member(user['id'])
                kwargs['member'] = member
                return render_template("first_time_user.html", **kwargs)
        else:
            content = render_template_string_or_file(template_file, template_string, **kwargs)
            # we really should not ever get here, but just in case
            member={"user": "unknown", "admin": False }
            kwargs['member'] = member
            return render_template('base.html', content=content, **kwargs)

class NotAdminMemberException(Exception):
    def __init__(self):
        super().__init__("Not an admin member")


def verify_admin_member(user):
    member = verify_member_registration(user)
    if member.get('level') == 10:
        return member
    else:
        raise NotAdminMemberException()
        
def get_member_id(context):
    member_id = None
    user = context.get('user', None)
    if user:
        member_id = user.get('sub', None)
    return member_id
        