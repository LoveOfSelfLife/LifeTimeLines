from flask_restx import Namespace, Resource, fields
from flask import request, url_for, redirect
from werkzeug.utils import secure_filename
import os
import photosapi as papi
from common.credentials import get_credentials, SCOPES

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
        try:
            test_env_var = os.environ['TEST_ENV_VARIABLE']
            print(f'test_env_var: {test_env_var}')
        except KeyError:
            print('variable not set')
        
        credentials = get_credentials(SCOPES)

        if not credentials:
            doauth_url = url_for('auth_do_auth')
            # doauth_url = self.api.url_for('auth_do_auth')
            return redirect(doauth_url)

        api = papi.PhotosApi()
        result_list = api.get_albums(credentials)

        result = dict()
        result['album_list'] = result_list

        return result
            
        return [{"id": 101, "status": "processing"}, {"id": 102, "status": "success"}]
 
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
