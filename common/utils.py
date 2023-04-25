import random
import hashlib
import datetime
import datetimerange

def generate_unique_id(table='', partition=''):
    iso = datetime.datetime.now().isoformat()
    t = f'{table}-{partition}-{iso}-{random.randint(0,5000)}'.encode()
    return hashlib.sha1(t).hexdigest()

def break_up_date_range_into_chunks(start_dt, end_dt, num_days_per_chunk):
    gap_dt = (end_dt - start_dt)
    # handle the case for gaps of less than one day; this essential "rounds up"
    if gap_dt.days == 0 and gap_dt.total_seconds() > 0:
        gap = 1
    else:
        gap = gap_dt.days
    for b,e in [(x,x+num_days_per_chunk) for x in range(0, gap, num_days_per_chunk)]:
        b_days = datetime.timedelta(days=b)
        e_days = datetime.timedelta(days=e)
        all_days = datetime.timedelta(days=gap)
        yield datetimerange.DateTimeRange(start_dt + b_days, start_dt + e_days if e < gap else start_dt + all_days)
