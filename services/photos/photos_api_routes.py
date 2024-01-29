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

@ns.route('/album-sync-op/<album_id>')
class ActorEntityAlbums(Resource):
    def post(self, album_id):
        album_sync_mgr = AlbumsSyncMgr()
        sync_result = album_sync_mgr.sync_album(album_id)
        return sync_result


@ns.route('/unsynced-photos-ranges')
class UnsyncedPhotoRanges(Resource):
    def get(self):
        photos_sync_mgr = PhotosSyncMgr()

        unsynced_ranges = photos_sync_mgr.get_unexplored_date_ranges(30)

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

@ns.route('/albums/<album_id>')
@ns.param('album_id', 'The album id')
class Album(Resource):
    '''items in an albumm'''
    # @ns.doc('get album items')
    def get(self, album_id):
        ts = None

        parser = reqparse.RequestParser()
        parser.add_argument("end", type=str)
        end = request.args.getlist("end")

        if end:
            ts = datetime.datetime.fromisoformat(end[0])
        
        api = GooglePhotosApi(get_credentials())

        album_items = api.get_album_items(album_id, ts)

        return list(album_items)

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


