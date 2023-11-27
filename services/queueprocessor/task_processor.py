
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


"""

def execute_task(task_json):
    service = task_json.get('service', 'echo')
    method = task_json.get('method', 'get')
    path = task_json.get('path', '/')
    body = task_json.get('body', "")

    URL=f'http://{service}.ltl.richkempinski.com{path}'
    if method == 'get':
        resp = requests.get(URL)
        return resp.json()
    if method == 'post':
        resp = requests.post(URL, data=body)
        return resp.json()
