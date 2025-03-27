from hashlib import sha256
import json
from datetime import datetime

def generate_id(context):
    t = datetime.now()    
    hash = sha256()
    hash.update(bytes(t.strftime("%Y%m%d%H%M%S-%f"), 'utf-8'))
    h = hash.hexdigest()
    alphanum = convert_to_alphanumeric(context)
    id = f'{alphanum}{h[0:16]}'
    return id

def convert_to_alphanumeric(s):
    """Convert a string to alphanumeric characters only."""
    return "".join([c for c in s if c.isalnum()])
