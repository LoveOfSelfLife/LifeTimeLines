
import requests

"""
{
    "service": "test",
    "method": "post",
    "path": "/create-something"
    "body": "{ this is data }"
}
{
    "service": "wgt",
    "method": "get",
    "path": "/solr/wgt_core/admin/ping",
    "body": ""
}
{
    "service": "entities",
    "method": "get",
    "path": "/Persons",
    "body": ""
}
{
    "service": "entities",
    "method": "get",
    "path": "/locations",
    "body": ""
}
{
    "service": "feapp",
    "method": "get",
    "path": "/fe",
    "body": ""
}

{
    "service": "feapp",
    "method": "get",
    "path": "/fe/solr",
    "body": ""
}

"""

def execute_task(task_json, token):
    service = task_json.get('service', 'echo')
    method = task_json.get('method', 'get')
    path = task_json.get('path', '/')
    body = task_json.get('body', "")

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
