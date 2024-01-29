
from datetimerange import DateTimeRange
import datetime

def load_date_ranges(ranges_store_iterator):
    ranges = [DateTimeRange(r['startDate'], r['endDate']) for r in ranges_store_iterator]
    return sorted(ranges, key=lambda d: d.start_datetime,reverse=False)

def get_first_unexplored_date_range(explored_date_ranges, min_date_iso, max_date_iso):
    min_date_dt = datetime.datetime.fromisoformat(min_date_iso).replace(tzinfo=None)
    curr = min_date_dt
    for range in explored_date_ranges:
        gap = curr - range.start_datetime
        # if gap.days != 0:
        if gap.total_seconds() > 0:
            return DateTimeRange(curr, range.start_datetime)
        else:
            curr = range.end_datetime
    max_date_dt = datetime.datetime.fromisoformat(max_date_iso).replace(tzinfo=None)
    gap = max_date_dt - curr
    # if gap != 0:
    if gap.total_seconds() > 0:    
        return DateTimeRange(curr, max_date_dt)
    return None

def get_unexplored_date_ranges(explored_date_ranges, min_date_iso, max_date_iso):
    min_date_dt = datetime.datetime.fromisoformat(min_date_iso).replace(tzinfo=None)
    curr = min_date_dt
    for range in explored_date_ranges:
        gap = curr - range.start_datetime
        # if gap.days != 0:
        if gap.total_seconds() > 0:
            yield DateTimeRange(curr, range.start_datetime)
        curr = range.end_datetime
    max_date_dt = datetime.datetime.fromisoformat(max_date_iso).replace(tzinfo=None)
    gap = max_date_dt - curr
    # if gap != 0:
    if gap.total_seconds() > 0:    
        yield DateTimeRange(curr, max_date_dt)

def add_range(range, date_ranges):
    date_ranges_copy = date_ranges.copy()
    date_ranges_copy.append(range)
    return sorted(date_ranges_copy, key=lambda d: d.start_datetime,reverse=False)

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
    while p < len(date_ranges) - 1:
        date_ranges, p = merge_pairs(date_ranges, p)
    return date_ranges

def shift_date_and_round_to_day(date_dt, delta_days):
    d = datetime.datetime(year = date_dt.year, month=date_dt.month, day=date_dt.day, tzinfo=date_dt.tzinfo)
    return d + datetime.timedelta(days=delta_days)

def break_up_date_range_into_chunks(start_dt, end_dt, num_days_per_chunk):
    chunks = list()
    gap_dt = (end_dt - start_dt)
    # if the gap is less than the size of a chunk, then just return the existing range and be done with it
    if gap_dt.days < num_days_per_chunk:
        chunks.append( DateTimeRange(start_dt, end_dt) )
    else:
        # handle the case for gaps of less than one day; this essential "rounds up"
        if gap_dt.days == 0 and gap_dt.total_seconds() > 0:
            gap = 1
        else:
            gap = gap_dt.days
        for b,e in [(x,x+num_days_per_chunk) for x in range(0, gap, num_days_per_chunk)]:
            b_days = datetime.timedelta(days=b)
            e_days = datetime.timedelta(days=e)
            all_days = datetime.timedelta(days=gap)
            chunks.append( DateTimeRange(start_dt + b_days, start_dt + e_days if e < gap else start_dt + all_days) )
    return chunks


if __name__ == '__main__':
    print("in main")

