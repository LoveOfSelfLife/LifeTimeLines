import random
import hashlib
import datetime
from sonyflake import SonyFlake

def generate_unique_id(table='', partition=''):
    iso = datetime.datetime.now().isoformat()
    t = f'{table}-{partition}-{iso}-{random.randint(0,5000)}'.encode()
    return hashlib.sha1(t).hexdigest()

def generate_digest(s: str):
    return hashlib.sha256(s.encode()).hexdigest()

def to_base62(number):
  """Converts a number to base62.
  Args:
    number: The number to convert.
  Returns:
    The number in base62.
  """

  if number < 0:
    raise ValueError("Number must be non-negative.")

  base62_digits = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
  result = ""
  while number > 0:
    result += base62_digits[number % 62]
    number //= 62

  return result[::-1]

class IDGenerator :
    generator = SonyFlake()
    def __init__(self):
        pass
    @staticmethod
    def gen_id():
        n = IDGenerator.generator.next_id()
        return to_base62(n)
    
