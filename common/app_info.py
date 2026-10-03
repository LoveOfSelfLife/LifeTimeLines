import os
from flask import current_app
from common.env_context import Env

def get_current_app_metadata():
    return current_app.config.get('APP_METADATA', {})

def get_current_app_id():
    metadata = get_current_app_metadata()
    return metadata.get('app_id', None)

def get_current_app_name():
    metadata = get_current_app_metadata()
    return metadata.get('title', None)

def get_current_template_folder():
    # Blueprint template_folder is relative to the blueprint module, so use an absolute path.
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
