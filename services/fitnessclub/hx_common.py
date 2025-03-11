from flask import render_template, request
from active_fitness_registry import get_active_fitness_entity_names
from member_info import MembershipRegistry, get_user_info_from_token

class FirstTimeUserException(Exception):
    def __init__(self):
        super().__init__("First time user")


class UnregisteredMemberException(Exception):
    def __init__(self):
        super().__init__("Unregistered member")

def verify_registered_member(user):
    members = MembershipRegistry()
    if not members.check_if_member(user['id']):
        raise FirstTimeUserException()
    else:
        user = members.get_member(user['id'])
    if user.get('level') == 0:
        raise UnregisteredMemberException()
    return user

def is_admin_member(user):
    members = MembershipRegistry()
    member = members.get_member(user['id'])
    return member.get('level') == 10

def hx_render_template(template, **kwargs):

    if request.headers.get("HX-Request"):
        return render_template(template, **kwargs)
    else:
        if kwargs.get('context', None) is not None:
            user = get_user_info_from_token(kwargs.get('context', None))
            try:
                member = verify_registered_member(user)
                return render_template('base.html', 
                                    content=render_template(template, **kwargs), 
                                    ctx={"configs":get_active_fitness_entity_names(), 
                                                        "user": member.get('name'), 
                                                        "admin": is_admin_member(member)} )

            except UnregisteredMemberException as e:
                print(f"User not registered: {e}")
                return render_template("unregistered_member.html", ctx = { "user": user.get('name'), "email": user.get('email') })
            
            except FirstTimeUserException as e:
                members = MembershipRegistry()
                members.add_member(user)
                print(f"First time user: {e}")
                return render_template("first_time_user.html", ctx = { "user": user.get('name'), "email": user.get('email') })
        else:
            return render_template('base.html', 
                                content=render_template(template, **kwargs), 
                                ctx={"configs":get_active_fitness_entity_names(), 
                                                    "user": "unknown",
                                                    "admin": False })

class NotAdminMemberException(Exception):
    def __init__(self):
        super().__init__("Not an admin member")


def verify_admin_member(user):
    member = verify_registered_member(user)
    if member.get('level') == 10:
        return member
    else:
        raise NotAdminMemberException()
        


        
