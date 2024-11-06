import requests
import json
import logging
from datetime import datetime, timedelta

def retrieve_unsynced_mediaitem_dateranges_fn(after, before, daysgap, token=None, instance_id=None):
    print(f"retrieve_unsynced_mediaitem_dateranges_fn(after={after}, before={before}, daysgap={daysgap})")

    # service = 'photos'
    # path=f"/photos/unsynced-photos-ranges?start_dt_iso={after}&end_dt_iso={before}&gap_days={daysgap}"

    # logging.info(f"path={path}")
    # logging.info(f"token: {'*******' if token else 'None'}")

    # URL=f'https://{service}.ltl.richkempinski.com{path}'
    # headers={'Authorization': 'Bearer ' + token}
    # resp = requests.get(URL, verify=False, headers=headers)

    # logging.info(f'retrieve_unsynced_mediaitem_dateranges_fn: response status:  {resp.status_code}')

    # return resp.json(), resp.status_code    
    ranges =   [ 
            {
                "start": "2024-08-07T00:00:00",
                "end": "2024-09-06T00:00:00"
            },
            {
                "start": "2024-09-06T00:00:00",
                "end": "2024-10-06T00:00:00"
            },
            {
                "start": "2024-10-06T00:00:00",
                "end": "2024-10-19T00:00:00"
            }
    ]

    return ranges, 200

def retrieve_entity_album_list_fn(token=None, instance_id=None):
    print(f"retrieve_entity_album_list_fn()")
    # service = 'photos'
    # path = '/photos/actor-entity-albums'

    # logging.info(f'path={path}')
    # logging.info(f"token: {'*******' if token else 'None'}")

    # URL=f'https://{service}.ltl.richkempinski.com{path}'
    # headers={'Authorization': 'Bearer ' + token}
    # resp = requests.get(URL, verify=False, headers=headers)

    # logging.info(f'retrieve_entity_album_list_fn: response status:  {resp.status_code}')

    # return resp.json(), resp.status_code
    actor_entity_albums =  [
            {
                "albumId": "AHD6C9V7tKNuAOgP-ZB-my0jTSMcGRL5ToWVnl1km7pucwV_xqYFY2VX06jwksoOgdska68WorOR",
                "albumName": "Mike_Hogan_Photos_Album",
                "latestPhotoInAlbumTime": "2024-02-24T00:18:36+00:00"
            },
            {
                "albumId": "AHD6C9XGwgrqNZxvNTpbJtTGxg3udZhCVThmdV7kpBI4pM016QEtP9zUecXKFV37emoIxOwc-o73",
                "albumName": "Mark_Y_Photos_Album",
                "latestPhotoInAlbumTime": "2024-02-04T02:57:00+00:00"
            },
            {
                "albumId": "AHD6C9WoeynRsWPtdo6rs60WPP9VggU-stkDLinZxIStLIhrTM4KpTj8eijE68aweuXOvZ_4qVBe",
                "albumName": "John_Mason_Photos_Album",
                "latestPhotoInAlbumTime": "2023-09-13T00:12:19Z"
            },
            {
                "albumId": "AHD6C9V3-J4ibACRXcKe0jFeknbvxRNJjnF9Gsi-Wuvy73sxoHi5CYvjMhZ8iS19KvnHiqSAbYuF",
                "albumName": "Joe_Fiamingo_Photos_Album",
                "latestPhotoInAlbumTime": None
            },
            {
                "albumId": "AHD6C9X-Ru_QKvsB4fWH070iBbQLN2k_lAfTXZMaHRsyP88-dSAh7FJ4cFEgwo6Q7VauJNcAQglq",
                "albumName": "Charlie_Meyer_Photos_Album",
                "latestPhotoInAlbumTime": "2024-02-04 02:57:00+00:00"
            }
    ]

    return actor_entity_albums, 200
