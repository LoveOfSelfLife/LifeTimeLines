import requests
import json

def foo(x,y,z):
    print(f"{z}: {x+y}")
    
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
        
