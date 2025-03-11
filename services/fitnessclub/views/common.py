from flask import render_template, request
from active_fitness_registry import get_active_fitness_entity_names
from services.fitnessclub.hx_common import is_admin_member
from member_info import MembershipRegistry, get_user_info_from_token
from services.fitnessclub.hx_common import FirstTimeUserException, UnregisteredMemberException, verify_registered_member


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
        


        
