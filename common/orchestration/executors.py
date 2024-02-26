import requests
import json

def foo(x,y):
    print(f"x: {x}, y: {y}, x+y: {x+y}, x*y: {x*y}")
    return ({ "x": x, "y": y, "x+y": x+y, "x*y": x*y }, 200)

def sync_mediaitems_in_daterange_fn(range, gap, token=None):
    s = range['start']
    e = range['end']
    g = gap
    return (f"GOT: {s}-{e}-{g}", 200)

def retrieve_unsynced_mediaitem_dateranges_fn(after, before, daysgap, token=None):
    result = [{ "start": "20200301", "end": "20200401"},
              { "start": "20200401", "end": "20200501"},
              { "start": "20200501", "end": "20200601"},
              { "start": "20200601", "end": "20200701"},
              { "start": "20200701", "end": "20200801"}
    ]
    return (result, 200)

def get_last_processed_timestamp_fn(token=None):
        result = { "timestamp": "20190301" }
        return (result, 200)

from datetime import datetime, timedelta

def curate_mediaitems_fn(timestamp, days=365, token=None):
    ts = datetime.fromisoformat(timestamp) 
    ts = ts + timedelta(int(days))
    if ts > datetime.now():
        return (None, 404)
    else:
        return (ts.isoformat(), 200)

def task_once1_fn(x, token=None):
    print(f"task_once1_fn(x={x})")
    return ([f"#1-task_once1_fn(x={x})", f"#2-task_once1_fn(x={x})"], 200)

def task_once2_fn(y, token=None):
    print(f"task_once2_fn(y={y})")
    return ([f"#1-task_once2_fn(y={y})", f"#2-task_once2_fn(y={y})"], 200)

def task_iterate_fn(in1, in2, token=None):
    print(f"task_iterate_fn(in1={in1}, in2={in2})") 
    return (f"task_iterate_fn(in1={in1}, in2={in2})", 200)

def task_iterate_iterate_fn(in1, in2, token=None):
    print(f"task_iterate_iterate_fn(in1={in1}, in2={in2})")
    return (f"task_iterate_iterate_fn(in1={in1}, in2={in2})", 200)
    
def task_repeat_fn(n, output=None, token=None):
    print(f"task_repeat_fn(n={n}, output={output})")
    print(f"task_repeat_fn(n={n})")
    if output is None:
        num_left = 4
    else:
        num_left = int(output.get("num_times",1)) - 1
    if num_left <= 0:
        return ({ "num_times" : 0 }, 404)
    return ({ "num_times" : num_left }, 200)

def task_iterate_repeat_fn(in1, output=None, token=None):
    print(f"task_iterate_repeat_fn(in1={in1}, output={output})")
    # return (f"task_iterate_repeat_fn(in1={in1}, output={output})", 200)
    if output is None:
        num_left = 3
    else:
        num_left = int(output.get("num_times",1)) - 1
    if num_left <= 0:
        return ({ "num_times" : 0 }, 404)
    return ({ "num_times" : num_left }, 200)
    
def task_iterate_iterate_repeat_fn(in1, in2, output=None, token=None):
    print(f"task_iterate_iterate_repeat_fn(in1={in1}, in2={in2},  output={output})")    
    # return (f"task_iterate_iterate_repeat_fn(in1={in1}, in2={in2}, output={output})", 200)
    if output is None:
        num_left = 2
    else:
        num_left = int(output.get("num_times",1)) - 1
    if num_left <= 0:
        return ({ "num_times" : 0 }, 404)
    return ({ "num_times" : num_left }, 200)

    # service = 'photos'
    # path = '/photos/unsynced-photos-ranges'

    # URL=f'https://{service}.ltl.richkempinski.com{path}'
    # headers={'Authorization': 'Bearer ' + token}

    # resp = requests.get(URL, verify=False, headers=headers)
    # print(f'response status:  {resp.status_code}')
    # resp.encoding = 'utf-8'
    # # return resp.json()
    # return resp.text, resp.status_code


# def sync_mediaitems_in_daterange_fn(date_range_object, token):
#     service = 'photos'
#     path = '/photos/unsynced-photos-ranges'

#     URL=f'https://{service}.ltl.richkempinski.com{path}'
#     headers={'Authorization': 'Bearer ' + token}

#     resp = requests.get(URL, verify=False, headers=headers)
#     print(f'response status:  {resp.status_code}')
#     resp.encoding = 'utf-8'
#     # return resp.json()
#     return resp.text

def call_api(service, method, path, body, token=None):
    print(f"call_api({service}, {method}, {path}, {body}, TOKEN)")
    return (json.dumps({"result": [1,2,3,4,5]}), 200)

    URL=f'https://{service}.ltl.richkempinski.com{path}'
    headers={'Authorization': 'Bearer ' + token}
    print(headers)
    print(f'URL:  {URL}')
    if method == 'get':
        resp = requests.get(URL, verify=False, headers=headers)
        print(f'response status:  {resp.status_code}')
        resp.encoding = 'utf-8'
        # return resp.json()
        return resp.text, resp.status_code
    if method == 'post':
        resp = requests.post(URL, data=body, verify=False, headers=headers)
        print(f'response status:  {resp.status_code}')        
        resp.encoding = 'utf-8'        
        # return resp.json()
        return resp.text, resp.status_code
        
