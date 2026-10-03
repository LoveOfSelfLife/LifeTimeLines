from flask import Blueprint

from common.app_info import get_current_template_folder

def create_blueprint(root, name):
    return Blueprint(root, name, template_folder=get_current_template_folder())  
