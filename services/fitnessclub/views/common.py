from flask import render_template, request
from services.fitnessclub.active_fitness_registry import get_active_fitness_entity_names
from services.fitnessclub.base import FirstTimeUserException, UnregisteredMemberException, is_admin_member, verify_registered_member
from services.fitnessclub.member_info import MembershipRegistry, get_user_info_from_token

def del_hx_render_template(template, **kwargs):
    # kwargs['configs'] = get_editable_entity_names()
    if request.headers.get("HX-Request"):
        return render_template(template, **kwargs)
    else:
        return render_template('base.html', 
                               content=render_template(template, **kwargs), 
                               ctx={"configs":get_active_fitness_entity_names()} )


def hx_render_template(template, **kwargs):

    if request.headers.get("HX-Request"):
        return render_template(template, **kwargs)
    else:
        user = get_user_info_from_token(kwargs.get('context'))
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


        
