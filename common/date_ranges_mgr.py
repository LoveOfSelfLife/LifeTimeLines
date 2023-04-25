from common.tables import EntityStore
from datetimerange import DateTimeRange
import datetime

def load_date_ranges_from_storage(domain, ranges_store):
    ranges = []
    for r in ranges_store.query("photos"):
        ranges.append(DateTimeRange(r['Start'], r['End']))
    return sorted(ranges, key=lambda d: d.start_datetime,reverse=False)

def get_unexplored_date_range(explored_date_ranges, min_date, max_date):
    min_date_dt = datetime.datetime.fromisoformat(min_date).replace(tzinfo=None)
    curr = min_date_dt
    for range in explored_date_ranges:
        gap = curr - range.start_datetime
        if gap.days != 0:
            return DateTimeRange(curr, range.start_datetime)
        else:
            curr = range.end_datetime
    max_date_dt = datetime.datetime.fromisoformat(max_date).replace(tzinfo=None)
    gap = max_date_dt - curr
    if gap != 0:
        return DateTimeRange(curr, max_date_dt)
    return None

def add_range(range, date_ranges):
    date_ranges_copy = date_ranges.copy()
    date_ranges_copy.append(range)
    return sorted(date_ranges_copy, key=lambda d: d.start_datetime,reverse=False)


def save_date_ranges_to_storage(domain, date_ranges, ranges_store):
    ranges_store.delete(domain)
    entities = []
    for r in date_ranges:
        entities.append({"RowKey": str(r.start_datetime), 
                         "PartitionKey": domain,
                         "Start": str(r.start_datetime), 
                         "End": str(r.end_datetime) }
                        )
    ranges_store.batch_insert(entities)
    return date_ranges

def can_merge(a,b):
    gap = a.end_datetime - b.start_datetime
    return gap.days == 0

def do_merge(a,b):
    return DateTimeRange(a.start_datetime, b.end_datetime)

def merge_pairs(inp,p):
    if (can_merge(inp[p], inp[p+1])):
        inp = inp[0:p] + [do_merge(inp[p], inp[p+1])] + inp[p+2:]
        np = p
    else:
        inp = inp[0:p] + [inp[p],inp[p+1]] + inp[p+2:]
        np = p+1
    return inp, np

def coaslesc_ranges(date_ranges):
    p = 0
    while True:
        inplen = len(date_ranges)        
        if p+1 >= inplen:
            break
        date_ranges, p = merge_pairs(date_ranges, p)
    return date_ranges

if __name__ == '__main__':
    print("in main")
