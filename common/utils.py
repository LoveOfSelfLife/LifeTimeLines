import random
import hashlib
import datetime

def generate_unique_id(table='', partition=''):
    iso = datetime.datetime.now().isoformat()
    t = f'{table}-{partition}-{iso}-{random.randint(0,5000)}'.encode()
    return hashlib.sha1(t).hexdigest()


