from flask_restx import Namespace, Resource, reqparse, fields
from flask import request, url_for, redirect, jsonify


import datetime
from common.entities.journal_day import JournalDay
from common.entity_store import EntityStore

from googlephotosapi import GooglePhotosApi
from common.google_credentials import get_credentials
from photos_sync import PhotosSyncMgr
from albums_sync import AlbumsSyncMgr

ns = Namespace('photos', description='services to sync with google photos')

@ns.route('/actor-entity-albums')
class ActorEntityAlbums(Resource):
    def get(self):
        album_sync_mgr = AlbumsSyncMgr()

        ae_albums = album_sync_mgr.get_actor_entity_albums()

        return list(ae_albums)

range_parser = reqparse.RequestParser()
range_parser.add_argument("start_dt_iso", type=str)
range_parser.add_argument("end_dt_iso", type=str)
range_parser.add_argument("gap_days", type=int)

@ns.route('/unsynced-photos-ranges')
class UnsyncedPhotoRanges(Resource):
    @ns.expect(range_parser)
    def get(self):
        photos_sync_mgr = PhotosSyncMgr()
        args = range_parser.parse_args()
        between_start = args['start_dt_iso']
        between_end = args['end_dt_iso']
        min_days = args['gap_days']

        # return { "args" : f"start: {args['start']} end: {args['end']}  gap: {args['gap']}" }
        unsynced_ranges = photos_sync_mgr.get_unexplored_date_ranges(between_start, between_end, min_days)

        return list(unsynced_ranges)

resource_fields = ns.model('Resource', {
    'start': fields.String,
    'end': fields.String
})

@ns.route('/sync-photos-op/')
class SyncPhotosOp(Resource):
    @ns.expect(resource_fields)
    def post(self):
        json_data = request.get_json(force=True)
        startdate_iso = json_data['start']
        enddate_iso = json_data['end']
        try:
            from_dt = datetime.datetime.fromisoformat(startdate_iso)
            to_dt = datetime.datetime.fromisoformat(enddate_iso)      
            photos_sync_mgr = PhotosSyncMgr()
            result = photos_sync_mgr.sync_photos_in_date_range(from_dt, to_dt)  
            return result
            # return jsonify(s=str(from_dt), e=str(to_dt))
        except ValueError:
            return "bad date format", 400
    
@ns.route('/albums')
class Albums(Resource):
    '''Show a single operation item and lets you delete them'''
    # @ns.doc('get albums')
    def get(self):

        api = GooglePhotosApi(get_credentials())

        album_list = api.get_entity_albums()
        
        result = dict()
        result['album_list'] = list(album_list)

        return result


@ns.route('/incremental-album-sync-op/<album_id>')
@ns.param('album_id', 'Album id')
class AlbumSyncOp(Resource):
    '''used to synchonize an album items incrementally. 
    By synchonize, we mean to fetch the items for an album from google photos and store them in the entity store.
    The process is incremental in that the items are fetched in pages, and the next page token is used to fetch the next page of items.

    The first time the client calls this endpoing, they provide just the album id and the number of items to sync in that call.  The next page token should be None.
    The response back to the client will be the number of items sync, as well as am encoded token that the client will use in subsequent calls to sync the next batch of items.
    If the encoded token is None, then the client knows that all items have been synced.
    In that series of calls, the number of items should always be the same as the first call.
    '''
    # TODO: this really should be a POST, but I'm using GET for now to make it easier to test
    @ns.doc(params={'next': {'description': 'opaque next page token', 'in': 'query', 'type': 'str'},
                    'num': {'description': 'number of items to sync', 'in': 'query', 'type': 'int'}})
    def get(self, album_id):
        continuation_token = request.args.get('next')
        num_items = request.args.get('num')

        if not num_items:
            num_items = 100

        album_sync_mgr = AlbumsSyncMgr()
        sync = album_sync_mgr.sync_album_items_incrementally(album_id, num_items, continuation_token)

        return { "num_items" : len(sync['items']), "next" : sync['continuation_token'] }

# @ns.route('/albums/<album_id>')
# @ns.param('album_id', 'The album id')
# class Album(Resource):
#     '''get items in an albumm'''
#     # query params here
#     @ns.doc(params={'end': {'description': 'iso datetime', 'in': 'query', 'type': 'str'},
#                     'next': {'description': 'next page token', 'in': 'query', 'type': 'str'},
#                     'num': {'description': 'number of items', 'in': 'query', 'type': 'int'}})
#     def get(self, album_id):
#         ts = None
#         end = request.args.get('end')
#         next_page = request.args.get('next')
#         num_items = request.args.get('num')

#         if not num_items:
#             num_items = 100

#         if end:
#             ts = datetime.datetime.fromisoformat(end)
        
#         api = GooglePhotosApi(get_credentials())

#         # returns {"next_page_token": nextPageToken, "items": album_item_list}
#         album_items = api.sync_album_items_incrementally(album_id, num_items, next_page, ts)

#         return { "items" : album_items['items'], "next" : album_items['next_page_token'] }

@ns.route('/category/<category>')
@ns.param('category', 'The category')
class Category(Resource):
    '''items in an albumm'''

    def get(self, category):
        ts = None

        parser = reqparse.RequestParser()
        parser.add_argument("end", type=str)
        end = request.args.getlist("end")

        if end:
            ts = datetime.datetime.fromisoformat(end[0])
        
        api = GooglePhotosApi(get_credentials())

        category_items = api.get_category_items(category, ts)

        return list(category_items)

@ns.route('/items')
class MediaItems(Resource):
    '''all items'''
    def get(self):
        '''Fetch a given resource'''
        parser = reqparse.RequestParser()
        parser.add_argument("start", type=str)
        parser.add_argument("end", type=str)
        start = request.args.getlist("start")
        end = request.args.getlist("end")
        if not start or not end:
            return []

        start = start[0]
        end = end[0]
        start_dt = datetime.datetime(int(start[0:4]), int(start[4:6]), int(start[6:8]))
        end_dt = datetime.datetime(int(end[0:4]), int(end[4:6]), int(end[6:8]))
                                     
        api = GooglePhotosApi(get_credentials())

        mitems = api.get_media_items_in_datetime_range(start_dt, end_dt)

        return list(mitems)

@ns.route('/daterange')
class MediaItemExtents(Resource):
    '''get the min & max extents for all mediaitems '''
    def get(self):
        api = GooglePhotosApi(get_credentials())
        extent = api.get_media_items_daterange_extent()
        return { "start": extent['earliest'] , "end" : extent['latest'] }

@ns.route('/token')
class TokenRefresh(Resource):
    '''refresh token'''
    def get(self):
        '''refresh token'''
        if get_credentials() is None:
            auth_url = url_for('auth_do_auth')
            return redirect(auth_url)

        return "seems we have a good token"

@ns.route('/store')
class TestStore(Resource):
    '''get data from the entity store'''
    def get(self):
        '''get data'''
        if get_credentials() is None:
            auth_url = url_for('auth_do_auth')
            return redirect(auth_url)
        e = EntityStore()
        jrnl_items = list(e.list_items(JournalDay()))
        if jrnl_items and len(jrnl_items) > 0:    
            return jrnl_items[0]
        else:
            return []


