import requests
import json
import logging
from datetime import datetime, timedelta

def retrieve_unsynced_mediaitem_dateranges_fn(after, before, daysgap, token=None, instance_id=None):
    service = 'photos'
    path=f"/photos/unsynced-photos-ranges?start_dt_iso={after}&end_dt_iso={before}&gap_days={daysgap}"

    logging.info(f"path={path}")
    logging.info(f"token: {'*******' if token else 'None'}")

    URL=f'https://{service}.ltl.richkempinski.com{path}'
    headers={'Authorization': 'Bearer ' + token}
    resp = requests.get(URL, verify=False, headers=headers)

    logging.info(f'retrieve_unsynced_mediaitem_dateranges_fn: response status:  {resp.status_code}')

    return resp.json(), resp.status_code    

def retrieve_entity_album_list_fn(token=None, instance_id=None):
    service = 'photos'
    path = '/photos/actor-entity-albums'

    logging.info(f'path={path}')
    logging.info(f"token: {'*******' if token else 'None'}")

    URL=f'https://{service}.ltl.richkempinski.com{path}'
    headers={'Authorization': 'Bearer ' + token}
    resp = requests.get(URL, verify=False, headers=headers)

    logging.info(f'retrieve_entity_album_list_fn: response status:  {resp.status_code}')

    return resp.json(), resp.status_code
