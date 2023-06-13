import random
import hashlib
import datetime
from sonyflake import SonyFlake

def generate_unique_id(table='', partition=''):
    iso = datetime.datetime.now().isoformat()
    t = f'{table}-{partition}-{iso}-{random.randint(0,5000)}'.encode()
    return hashlib.sha1(t).hexdigest()

class IDGenerator :
    generator = SonyFlake()
    def __init__(self):
        pass
    @staticmethod
    def gen_id():
        return IDGenerator.generator.next_id()
