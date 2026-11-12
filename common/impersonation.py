from flask import session
import json

def start_impersonation(member_id):
    session['impersonating_member_id'] = member_id

def stop_impersonation():
    session.pop('impersonating_member_id', None)

def get_impersonated_member_id():
    return session.get('impersonating_member_id', None)
