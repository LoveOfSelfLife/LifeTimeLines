from flask_restx import Namespace, Resource, fields, reqparse
from flask import request, url_for, redirect
from werkzeug.utils import secure_filename
import os
import photosapi as papi
from common.credentials import get_credentials, GOOGLE_SCOPES
import datetime
ns = Namespace('photos', description='services to sync with google photos')

task_model = ns.model('sync', {
    'id': fields.Integer(readonly=True, description='The task unique identifier'),
    'task': fields.String(required=True, description='The task details')
})

@ns.route('/')
class SyncOperationsList(Resource):

    '''Shows all sync operations '''
    @ns.doc('list sync operations')
    def get(self):
        '''List all tasks'''
        return {'tasks': []}

 
    @ns.doc('create operation by posting a file')
    def post(self):
        file = request.files['file']
        if file:
            filename = secure_filename(file.filename)
            if os.path.isdir('/share/stage'):
                path = os.path.join('/share/stage', filename)
                file.save(path)
                return {"id": 0, "task" : f'saved to: {path}'}
            else:
                path = os.path.join('./', f"{filename}2")
                file.save(path)
                return {"id": 0, "task" : f'saved to: {path}'}
        else:
            return {"id": 0, "task" : "False" }

@ns.route('/<int:id>')
@ns.response(404, 'Operation not found')
@ns.param('id', 'The operation identifier')
class SyncOperation(Resource):
    '''Show a single operation item and lets you delete them'''
    @ns.doc('get sync operation')
    def get(self, id):
        '''Fetch a given resource'''
        # return DAO.get(id)
        return {"id": 101, "status": "processing"}
    
    @ns.doc('delete sync operation')
    @ns.response(204, 'Operation deleted')
    def delete(self, id):
        '''Delete a task given its identifier'''
        # DAO.delete(id)
        print(f'id: {id}')
        return '', 204

    def put(self, id):
        '''Update an operation given its identifier'''
        # return DAO.update(id, ns.payload)
        print(f'ns.payload: {ns.payload}')
        return '', 204

@ns.route('/albums')
class Albums(Resource):
    '''Show a single operation item and lets you delete them'''
    # @ns.doc('get albums')
    def get(self):

        api = papi.PhotosApi(get_credentials(GOOGLE_SCOPES))

        album_list = api.get_entity_albums()
        
        result = dict()
        result['album_list'] = album_list

        return result

@ns.route('/albums/<album_id>')
@ns.param('album_id', 'The album id')
class AlbumItems(Resource):
    '''items in an albumm'''
    # @ns.doc('get album items')
    def get(self, album_id):
        ts = None

        parser = reqparse.RequestParser()
        parser.add_argument("end", type=str)
        end = request.args.getlist("end")

        if end:
            ts = datetime.datetime.fromisoformat(end[0])
        
        api = papi.PhotosApi(get_credentials(GOOGLE_SCOPES))

        album_items = api.get_album_items(album_id, ts)

        return album_items

@ns.route('/category/<category>')
@ns.param('category', 'The category')
class CategoryItems(Resource):
    '''items in an albumm'''

    def get(self, category):
        ts = None

        parser = reqparse.RequestParser()
        parser.add_argument("end", type=str)
        end = request.args.getlist("end")

        if end:
            ts = datetime.datetime.fromisoformat(end[0])
        
        api = papi.PhotosApi(get_credentials(GOOGLE_SCOPES))

        category_items = api.get_category_items(category, ts)

        return category_items

@ns.route('/items')
class PhotosItems(Resource):
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
                                     
        api = papi.PhotosApi(get_credentials(GOOGLE_SCOPES))

        album_items = api.get_media_items(start_date, end_date)

        return album_items

@ns.route('/token')
class TokenRefresh(Resource):
    '''refresh token'''
    def get(self):
        '''refresh token'''
        if get_credentials(GOOGLE_SCOPES) is None:
            return redirect(url_for('auth_do_auth'))

        return "seems we have a good token"
    