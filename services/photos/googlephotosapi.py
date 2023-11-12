from googleapiclient.discovery import build
import re
import datetime 
    
API_NAME = 'photoslibrary'
API_VERSION = 'v1'

class GooglePhotosApi():

    def __init__(self, credentials=None):
        self.credentials = credentials
        pass

    def get_entity_albums(self):
        return self.get_albums(filter="Photos_Album")

    def get_albums(self, filter=""):

        service = build(API_NAME, API_VERSION, credentials=self.credentials, static_discovery=False)
        # album_list = []
        nextPageToken=None

        while True:
            resp = service.albums().list(pageToken=nextPageToken).execute()
            albums = resp.get('albums', [])
            nextPageToken = resp.get('nextPageToken', None)

            for a in albums:
                # TODO: generalize the filter to a reg expression
                if 'title' in a and a['title'].endswith(filter):
                        item = {
                            "title": a['title'],
                            "id": a['id']
                        }
                        yield item

            if nextPageToken is None:
                break

    def get_album_items(self, album_id, timestamp=None):
        service = build(API_NAME, API_VERSION, credentials=self.credentials, static_discovery=False)
        # items_list = []
        nextPageToken=None
        time_to_stop = lambda itemTime : False
        we_are_done = False

        while True:
            resp = service.mediaItems().search(body={'albumId': album_id, 
                                                     'pageSize': 100,
                                                    'pageToken': nextPageToken}).execute()
            mitems = resp.get('mediaItems')
            nextPageToken = resp.get('nextPageToken')

            for mi in mitems:
                if 'mediaMetadata' in mi and 'creationTime' in mi['mediaMetadata']:
            
                        if timestamp:
                            ct = datetime.datetime.fromisoformat(mi['mediaMetadata']['creationTime'])
                            cutoff = timestamp
                            if ct <= cutoff:
                                we_are_done = True
                                break
            
                        item = {
                            "id": mi['id'],
                            "creationTime": mi['mediaMetadata']['creationTime']
                        }
                # items_list.append(item)
                yield item
            # print(f"items_list: {len(items_list)}")
        
            if nextPageToken is None or we_are_done:
                break
        # return items_list

    def get_category_items(self, category, timestamp=None):
        service = build(API_NAME, API_VERSION, credentials=self.credentials, static_discovery=False)
        # items_list = []
        nextPageToken=None
        we_are_done = False

        while True:
            resp = service.mediaItems().search(body={'filters' : {
                                                        'contentFilter': {
                                                            'includedContentCategories' : [
                                                                category
                                                            ]
                                                        }
                                                    },
                                                    'pageSize': 100,
                                                'pageToken': nextPageToken}).execute()
            mitems = resp.get('mediaItems')
            nextPageToken = resp.get('nextPageToken')

            for mi in mitems:
                if 'mediaMetadata' in mi and 'creationTime' in mi['mediaMetadata']:
            
                        if timestamp:
                            ct = datetime.datetime.fromisoformat(mi['mediaMetadata']['creationTime'])
                            cutoff = timestamp
                            if ct <= cutoff:
                                we_are_done = True
                                break
            
                        item = {
                            "id": mi['id'],
                            "creationTime": mi['mediaMetadata']['creationTime']
                        }
                # items_list.append(item)
                yield item
            # print(f"items_list: {len(items_list)}")
        
            if nextPageToken is None or we_are_done:
                break

        # return items_list

    def get_media_items_in_datetime_range(self, start_dt, end_dt, max_mitems=0):
        start_date = {"year": start_dt.year, "month": start_dt.month, "day": start_dt.day}
        end_date = {"year": end_dt.year, "month": end_dt.month, "day": end_dt.day}
        return self.get_media_items(start_date, end_date, max_mitems=max_mitems)

    def get_media_items(self, start_date, end_date, max_mitems=0):
        service = build(API_NAME, API_VERSION, credentials=self.credentials, static_discovery=False)
        # items_list = []
        nextPageToken=None
        stop_after_max_mitems = False
        if max_mitems > 0:
             stop_after_max_mitems = True
        while True:
            body = {'filters': {
                                'dateFilter': {
                                    'ranges': {
                                        'startDate': {
                                            'year': start_date['year'],
                                            'month': start_date['month'],
                                            'day': start_date['day']
                                        },
                                        'endDate': {
                                            'year': end_date['year'],
                                            'month': end_date['month'],
                                            'day': end_date['day']
                                        }
                                    }
                                }
                            },
                            'pageSize': 100,
                            'pageToken': nextPageToken}
            resp = service.mediaItems().search(body=body).execute()
            mitems = resp.get('mediaItems')
            nextPageToken = resp.get('nextPageToken')
            if mitems is None:
                 break
            for mi in mitems:
                if 'mediaMetadata' in mi and 'creationTime' in mi['mediaMetadata']:
                        item = {
                            "id": mi['id'],
                            "creationTime": mi['mediaMetadata']['creationTime'],
                            "mimeType": mi['mimeType']
                        }

                # items_list.append(item)
                yield item
                max_mitems -= 1
            # print(f"items_list: {len(items_list)}")
            if nextPageToken is None:
                break
            if stop_after_max_mitems and max_mitems <= 0:
                break
        # return items_list

    def get_photo(self, photo_id, credentials):
        service = build(API_NAME, API_VERSION, credentials=credentials,static_discovery=False)
        resp = service.mediaItems().get(mediaItemId=photo_id).execute()
        return resp

    # get metadata for a set of media items in one call
    def get_photos(self, mitem_ids, credentials):
        """
        batchGet method

        media_ids = df_media_items['id'][107:112].to_list()
        response = service.mediaItems().batchGet(mediaItemIds=media_ids).execute()
        print(pd.DataFrame(response.get('mediaItemResults'))['mediaItem'].apply(pd.Series))
        """ 
        pass

    def get_media_items_daterange(self):
        oldest = self.get_oldest_media_item()
        newest = self.get_newest_media_item()
        return (oldest['creationTime'], newest['creationTime'])

    def get_oldest_media_item(self):
        return self._get_sorted_media_items(num_items=1, newest_first=False)
    
    def get_newest_media_item(self):
         return self._get_sorted_media_items(num_items=1, newest_first=True)
    
    def _get_sorted_media_items(self, num_items, newest_first):
        service = build(API_NAME, API_VERSION, credentials=self.credentials,static_discovery=False)
        BEGINNING_OF_TIME = {
                            "year": 1958,
                            "month": 1,
                            "day": 1
                            }
        END_OF_TIME = {
                    "year": 2099,
                    "month": 12,
                    "day": 31
                    }
        req = {
            "pageSize": num_items,
            "filters": {
                "dateFilter": {
                    "ranges": [
                            {
                            "startDate": BEGINNING_OF_TIME,
                            "endDate": END_OF_TIME
                            }
                    ]
                }
            },
            "orderBy": "MediaMetadata.creation_time" + (" desc" if newest_first else "")
        }
        resp = service.mediaItems().search(body=req).execute()
        
        return self._extract_id_and_time(resp)

    def _extract_id_and_time(self, resp):
        if 'mediaItems' in resp:
            mi = resp['mediaItems'][0]
            return {
                'id': mi['id'],
                'url': mi['productUrl'],
                'creationTime': mi['mediaMetadata']['creationTime']
            }
        return { "id": "", "creationTime": ""}
    