from flask_restx import Namespace, Resource, reqparse
from flask import request, url_for, redirect
import datetime

from googlephotosapi import GooglePhotosApi
from common.google_credentials import get_credentials
from photos_sync import PhotosSyncMgr

ns = Namespace('photos', description='services to sync with google photos')
    
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

        start_date = datetime.datetime(int(start[0:4]), int(start[0][4:6]), int(start[0][6:8]))
        end_date = datetime.datetime(int(end[0:4]), int(end[0][4:6]), int(end[0][6:8]))
                                     
        api = GooglePhotosApi(get_credentials())

        album_items = api.get_media_items(start_date, end_date)

        return list(album_items)

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

