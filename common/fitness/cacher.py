import json
from flask import current_app
def get_cache_value(key: str):
    """
    Retrieve a value from the cache using the provided key.
    """
    redis_client = current_app.config['SESSION_CACHELIB']
    v = redis_client.get(key)
    if v:
        return json.loads(v)
    return None

def set_cache_value(key: str, value):
    """
    Set a value in the cache with the provided key.
    """
    redis_client = current_app.config['SESSION_CACHELIB']
    redis_client.set(key, json.dumps(value))

def delete_from_cache(key: str):
    """
    Delete a value from the cache using the provided key.
    """
    redis_client = current_app.config['SESSION_CACHELIB']
    redis_client.delete(key)

