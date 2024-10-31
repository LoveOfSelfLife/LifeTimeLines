import requests
import json
import logging
from datetime import datetime, timedelta

def get_last_processed_timestamp_fn(token=None):
        result = { "timestamp": "20190301" }
        return (result, 200)

def curate_mediaitems_fn(timestamp, days=365, token=None):
    ts = datetime.fromisoformat(timestamp) 
    ts = ts + timedelta(int(days))
    if ts > datetime.now():
        return (None, 404)
    else:
        return (ts.isoformat(), 200)

def task_once1_fn(x, token=None):
    print(f"TEST task_once1_fn(x={x})")
    return ([f"#1-task_once1_fn(x={x})", f"#2-task_once1_fn(x={x})"], 200)

def task_once2_fn(y, token=None):
    print(f"TEST task_once2_fn(y={y})")
    return ([f"#1-task_once2_fn(y={y})", f"#2-task_once2_fn(y={y})"], 200)

def task_iterate_fn(in1, in2, token=None):
    print(f"TEST task_iterate_fn(in1={in1}, in2={in2})") 
    return (f"task_iterate_fn(in1={in1}, in2={in2})", 200)

def task_iterate_iterate_fn(in1, in2, token=None):
    print(f"TEST task_iterate_iterate_fn(in1={in1}, in2={in2})")
    return (f"task_iterate_iterate_fn(in1={in1}, in2={in2})", 200)
    
def task_repeat_fn(n, output=None, token=None):
    print(f"TEST task_repeat_fn(n={n}, output={output})")
    if output is None:
        num_left = 4
    else:
        num_left = int(output.get("num_times",1)) - 1
    if num_left <= 0:
        return ({ "num_times" : 0 }, 404)
    return ({ "num_times" : num_left }, 200)

def task_iterate_repeat_fn(in1, output=None, token=None):
    print(f"TEST task_iterate_repeat_fn(in1={in1}, output={output})")
    # return (f"task_iterate_repeat_fn(in1={in1}, output={output})", 200)
    if output is None:
        num_left = 3
    else:
        num_left = int(output.get("num_times",1)) - 1
    if num_left <= 0:
        return ({ "num_times" : 0 }, 404)
    return ({ "num_times" : num_left }, 200)
    
def task_iterate_iterate_repeat_fn(in1, in2, output=None, token=None):
    print(f"TEST task_iterate_iterate_repeat_fn(in1={in1}, in2={in2},  output={output})")    
    # return (f"task_iterate_iterate_repeat_fn(in1={in1}, in2={in2}, output={output})", 200)
    if output is None:
        num_left = 2
    else:
        num_left = int(output.get("num_times",1)) - 1
    if num_left <= 0:
        return ({ "num_times" : 0 }, 404)
    return ({ "num_times" : num_left }, 200)

def call_api(service, method, path, body, token=None):
    print(f"TEST call_api({service}, {method}, {path}, {body}, TOKEN)")
    return (json.dumps({"result": [1,2,3,4,5]}), 200)

    # URL=f'https://{service}.ltl.richkempinski.com{path}'
    # headers={'Authorization': 'Bearer ' + token}
    # print(headers)
    # print(f'URL:  {URL}')
    # if method == 'get':
    #     resp = requests.get(URL, verify=False, headers=headers)
    #     print(f'response status:  {resp.status_code}')
    #     resp.encoding = 'utf-8'
    #     # return resp.json()
    #     return resp.text, resp.status_code
    # if method == 'post':
    #     resp = requests.post(URL, data=body, verify=False, headers=headers)
    #     print(f'response status:  {resp.status_code}')        
    #     resp.encoding = 'utf-8'        
    #     # return resp.json()
    #     return resp.text, resp.status_code
        
