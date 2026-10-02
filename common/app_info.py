from flask import current_app

def get_current_app_metadata():
    return current_app.config.get('APP_METADATA', {})

def get_current_app_id():
    metadata = get_current_app_metadata()
    return metadata.get('app_id', None)

def get_current_app_name():
    metadata = get_current_app_metadata()
    return metadata.get('title', None)


