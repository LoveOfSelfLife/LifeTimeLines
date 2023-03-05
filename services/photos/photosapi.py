from googleapiclient.discovery import build

API_NAME = 'photoslibrary'
API_VERSION = 'v1'

class PhotosApi():

    def __init__(self):
        pass

    def get_albums(self, credentials):

        service = build(API_NAME, API_VERSION, credentials=credentials, static_discovery=False)
        result_list = []
        
        myAblums = service.albums().list().execute()
        myAblums_list = myAblums.get('albums')
        for alb in myAblums_list:
            result_list.append(alb)
        return result_list

    def get_photo(self, photo_id, credentials):
        service = build(API_NAME, API_VERSION, credentials=credentials,static_discovery=False)
        resp = service.mediaItems().get(mediaItemId=photo_id).execute()
        return resp

    def get_album_items(self, album_id, credentials, next_page=None):

        service = build(API_NAME, API_VERSION, credentials=credentials,static_discovery=False)
        resp = service.mediaItems().search(body={'albumId': album_id, 
                                                 'pageToken': next_page}).execute()
        next_page_token = resp.get('nextPageToken', None)
        return (resp['mediaItems'], next_page_token)
