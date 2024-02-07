import requests
import json

def foo(x,y):
    print(f"x: {x}, y: {y}, x+y: {x+y}, x*y: {x*y}")
    return { "x": x, "y": y, "x+y": x+y, "x*y": x*y }

def sync_mediaitems_in_daterange_fn(range, gap):
    s = range['start']
    e = range['end']
    g = gap
    return f"GOT: {s}-{e}-{g}"

def retrieve_unsynced_mediaitem_dateranges_fn(after, before, daysgap):
    result = [{ "start": "20200301", "end": "20200401"},
              { "start": "20200401", "end": "20200501"},
              { "start": "20200501", "end": "20200601"},
              { "start": "20200601", "end": "20200701"},
              { "start": "20200701", "end": "20200801"}
    ]
    return result
    # return json.dumps(result)

    service = 'photos'
    path = '/photos/unsynced-photos-ranges'

    URL=f'https://{service}.ltl.richkempinski.com{path}'
    headers={'Authorization': 'Bearer ' + token}

    resp = requests.get(URL, verify=False, headers=headers)
    print(f'response status:  {resp.status_code}')
    resp.encoding = 'utf-8'
    # return resp.json()
    return resp.text


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

def call_api(service, method, path, body, token):
    print(f"call_api({service}, {method}, {path}, {body}, TOKEN)")
    return json.dumps({"result": [1,2,3,4,5]})

    URL=f'https://{service}.ltl.richkempinski.com{path}'
    headers={'Authorization': 'Bearer ' + token}
    print(headers)
    print(f'URL:  {URL}')
    if method == 'get':
        resp = requests.get(URL, verify=False, headers=headers)
        print(f'response status:  {resp.status_code}')
        resp.encoding = 'utf-8'
        # return resp.json()
        return resp.text
    if method == 'post':
        resp = requests.post(URL, data=body, verify=False, headers=headers)
        print(f'response status:  {resp.status_code}')        
        resp.encoding = 'utf-8'        
        # return resp.json()
        return resp.text
        
