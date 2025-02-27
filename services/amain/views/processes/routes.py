import json
from quart import Blueprint, render_template, request, Quart, websocket, Response
import asyncio
import aiohttp
import logging
import requests
from common.auth_requestor import AuthRequestor
from common.env_context import Env
from common.discovery import get_service_url

from ..common import hx_render_template
bp = Blueprint('processes', __name__, template_folder='templates')
import os
logger = logging.getLogger(__name__)

@bp.route('/')
async def root():
    return await hx_render_template('default.html')

@bp.route('/get-entities-sync', methods=['GET'])
async def get_entities_sync():
    logger.info('get_entities_sync()')
    response, status = await call_get_api_service('entities', '/Persons', {})
    return response

@bp.route('/get-entities-async', methods=['GET'])
async def get_entities_async():
    logger.info('get_entities_async()')
    response, status = await call_get_api_service('entities', '/Persons', {})
    return response

async def get_headers():
    scope = [f"api://{Env.AZURE_CLIENT_ID}/.default"]
    auth = AuthRequestor(Env.TENANT_ID, Env.AZURE_CLIENT_ID, Env.AZURE_CLIENT_SECRET, scope)
    token = auth.get_auth_token()
    headers={"Authorization": "Bearer " + token,
             "Content-Type": "application/json"}
    return headers

async def call_get_api_service(service, path, body):
    logger.info('call_get_api_service()')

    headers = await get_headers()
    URL_HOST_PORT = get_service_url(service)
    
    path = "/" + path if path[0] != '/' else path
    URL=f'{URL_HOST_PORT}{path}'
    
    logger.info(f'URL:  {URL}')

    resp = requests.get(URL, verify=False, headers=headers)
    logger.info(f'response status:  {resp.status_code}')        

    resp.encoding = 'utf-8'        
    return resp.text, resp.status_code

async def call_post_api_service(service, path, body):
    logger.info('call_api_service()')

    headers = await get_headers()
    URL_HOST_PORT = get_service_url(service)
    
    path = "/" + path if path[0] != '/' else path
    URL=f'{URL_HOST_PORT}{path}'
    
    logger.info(f'URL:  {URL}')

    resp = requests.post(URL, data=json.dumps(body), verify=False, headers=headers)
    print(f'response status:  {resp.status_code}')        
    resp.encoding = 'utf-8'        

    return resp.text, resp.status_code

from aiohttp import ClientSession

async def fetch_data(session, url, source, queue):
    try:
        headers = await get_headers()
        async with session.request("get", url, headers=headers) as response:
            response.raise_for_status()
            async for line in response.content:
                if line:
                    data_line = json.dumps({"source": source, "data": json.loads(line.decode())}) + "\n"
                    await queue.put(data_line)
    except aiohttp.ClientError as e:
        # If there's an error, still put something in the queue to notify the caller
        await queue.put(json.dumps({"error": f"Failed to fetch data from {source}: {str(e)}"}) + "\n")
    finally:
        # Signal that this source is done
        await queue.put(None)

@bp.route('/aggregate-data', methods=['GET'])
async def aggregate_data():
    URL_HOST_PORT = get_service_url('entities')
    url_1 = f'{URL_HOST_PORT}/Persons'
    url_2 = f'{URL_HOST_PORT}/Locations'

    external_api_url_1 = url_1
    external_api_url_2 = url_2

    async def stream_results():
        async with aiohttp.ClientSession() as session:
            queue = asyncio.Queue()

            # Start fetching data from both APIs concurrently
            task1 = asyncio.create_task(fetch_data(session, external_api_url_1, "api1", queue))
            task2 = asyncio.create_task(fetch_data(session, external_api_url_2, "api2", queue))

            done_count = 0
            total_tasks = 2

            while True:
                item = await queue.get()
                if item is None:
                    done_count += 1
                    if done_count == total_tasks:
                        # Both tasks completed
                        break
                else:
                    # Stream the data line directly to the client
                    yield item
                queue.task_done()

    return Response(stream_results(), content_type="application/json")
