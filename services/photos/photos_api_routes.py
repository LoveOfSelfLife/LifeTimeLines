from flask_restx import Namespace, Resource, reqparse, api
from flask import request, url_for, redirect
from werkzeug.utils import secure_filename
import os
import datetime

from googlephotosapi import GooglePhotosApi
from common.google_credentials import get_credentials, GOOGLE_SCOPES
from photos_sync import PhotosSyncMgr

photos_api_ns = Namespace('photos', description='services to sync with google photos')

@photos_api_ns.route('/sync-ops')
class PhotosSyncOperations(Resource):

    '''Shows all sync operations '''
    @photos_api_ns.doc('list sync operations')
    def get(self):
        '''List all sync operations '''
        sm = PhotosSyncMgr()
        return list(sm.list_operations())

    @photos_api_ns.doc('create a sync operation')
    def post(self):
        sm = PhotosSyncMgr()
        # request.data
        op = request.get_json()
        return sm.create_sync_operation(operation=op.get('operation','noop'), 
                                        domain=op.get('domain',None), 
                                        amount=op.get('amount',0))
    

@photos_api_ns.route('/<int:id>')
@photos_api_ns.response(404, 'Operation not found')
@photos_api_ns.param('id', 'The operation identifier')
class PhotosSyncOperation(Resource):

    @photos_api_ns.doc('get sync operation')
    def get(self, id):
        sm = PhotosSyncMgr()
        op = sm.get_operation(id)
        if op:
            return op
        else:
            return '', 404
    
    @photos_api_ns.doc('delete sync operation')
    @photos_api_ns.response(204, 'Operation deleted')
    def delete(self, id):
        '''Delete a task given its identifier'''
        sm = PhotosSyncMgr()
        sm.del_operation(id)
        return f'{id}', 204

    def put(self, id):
        '''Update a specific operation '''
        sm = PhotosSyncMgr()
        result = sm.update_operation(id, photos_api_ns.payload)
        return result, 204
    
@photos_api_ns.route('/albums')
class Albums(Resource):
    '''Show a single operation item and lets you delete them'''
    # @ns.doc('get albums')
    def get(self):

        api = GooglePhotosApi(get_credentials(GOOGLE_SCOPES))

        album_list = api.get_entity_albums()
        
        result = dict()
        result['album_list'] = album_list

        return result

@photos_api_ns.route('/albums/<album_id>')
@photos_api_ns.param('album_id', 'The album id')
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
        
        api = GooglePhotosApi(get_credentials(GOOGLE_SCOPES))

        album_items = api.get_album_items(album_id, ts)

        return album_items

@photos_api_ns.route('/category/<category>')
@photos_api_ns.param('category', 'The category')
class Category(Resource):
    '''items in an albumm'''

    def get(self, category):
        ts = None

        parser = reqparse.RequestParser()
        parser.add_argument("end", type=str)
        end = request.args.getlist("end")

        if end:
            ts = datetime.datetime.fromisoformat(end[0])
        
        api = GooglePhotosApi(get_credentials(GOOGLE_SCOPES))

        category_items = api.get_category_items(category, ts)

        return category_items

@photos_api_ns.route('/items')
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
                                     
        api = GooglePhotosApi(get_credentials(GOOGLE_SCOPES))

        album_items = api.get_media_items(start_date, end_date)

        return album_items

@photos_api_ns.route('/daterange')
class MediaItemExtents(Resource):
    '''get the min & max extents for all mediaitems '''
    def get(self):
        api = GooglePhotosApi(get_credentials(GOOGLE_SCOPES))
        oldest, newest = api.get_media_items_daterange()
        return { "start": oldest , "end" : newest }

@photos_api_ns.route('/token')
class TokenRefresh(Resource):
    '''refresh token'''
    def get(self):
        '''refresh token'''
        if get_credentials(GOOGLE_SCOPES) is None:
            return redirect(url_for('auth_do_auth'))

        return "seems we have a good token"

@photos_api_ns.route('/test')
class Tests(Resource):
    def get(self):
        sm = PhotosSyncMgr()
        ops = list(sm.list_operations())
        print(f"operations: {ops}")
        id = ops[0]['RowKey']

        op = sm.get_operation(id)
        print(f"opeation:  {op}")

        op = sm.update_operation(id)
        print(f"update opeation:  {id}")

        # op = sm.del_operation(id)
        # print(f"delete opeation:  {id}")

        return { "tests": True, "op": "get" }

    def post(self):
        return { "tests": True, "op": "post" }
