import json
from flask import current_app
def get_cache_value(key: str):
    """
    Retrieve a value from the cache using the provided key.
    """
    redis_client = current_app.config['SESSION_REDIS']
    v = redis_client.get(key)
    if v:
        return json.loads(v)
    return None

def set_cache_value(key: str, value):
    """
    Set a value in the cache with the provided key.
    """
    redis_client = current_app.config['SESSION_REDIS']
    redis_client.set(key, json.dumps(value))

def delete_from_cache(key: str):
    """
    Delete a value from the cache using the provided key.
    """
    redis_client = current_app.config['SESSION_REDIS']
    redis_client.delete(key)

def get_cache_hash_field(key: str, field: str):
    """Read one field of a Redis hash - used for atomic per-field updates (no read-modify-write of a whole blob)."""
    redis_client = current_app.config['SESSION_REDIS']
    v = redis_client.hget(key, field)
    if v:
        return json.loads(v)
    return None

def set_cache_hash_field(key: str, field: str, value):
    """Write one field of a Redis hash atomically, leaving all other fields untouched."""
    redis_client = current_app.config['SESSION_REDIS']
    redis_client.hset(key, field, json.dumps(value))

def get_cache_hash(key: str):
    """Read every field of a Redis hash as a dict."""
    redis_client = current_app.config['SESSION_REDIS']
    raw = redis_client.hgetall(key)
    if not raw:
        return {}
    result = {}
    for k, v in raw.items():
        field_name = k.decode('utf-8') if isinstance(k, bytes) else k
        result[field_name] = json.loads(v)
    return result

