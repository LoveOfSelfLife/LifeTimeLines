from flask_restx import Namespace, Resource, reqparse
from flask import request, url_for, redirect
import datetime

from googlephotosapi import GooglePhotosApi
from common.google_credentials import get_credentials
from photos_sync import PhotosSyncMgr

from photos_tasks import PHOTOS_TASKS

ns = Namespace('tasks', description='services to sync with google photos')

def is_task(task):
    return next((x for x in PHOTOS_TASKS if x['task_name'] == task), None)

@ns.route('/')
class PhotosTasks(Resource):

    '''Shows all photos tasks '''
    @ns.doc('list tasks')
    def get(self):
        '''List all tasks '''
        return [ t['task_name'] for t in PHOTOS_TASKS ]

@ns.route('/<task>')
@ns.response(404, 'Operation not found')
@ns.param('task', 'The specific identifier')
class PhotosTasksOperations(Resource):

    @ns.doc('get list of task instances created for a specific task')
    def get(self, task):
        # if task == 'status':
        #     return [{"gap": "gap"}, {"gap": "gap"}]
        # elif is_task(task):

        if is_task(task):
            return [ { "task": f"{task}", "id": 101, "status" : "success"}, 
                     { "task": f"{task}", "id": 102, "status" : "processing"}
                    ]
        else:
            return 'unknown task', 404
    
    def post(self, task):
        '''create a specific instance of task '''
        # sm = PhotosSyncMgr()
        # result = sm.update_operation(id, ns.payload)
        # return result, 204
        if is_task(task):
            return {'result': f'result-value: {task}', 'id': 103}
        else:
            return 'unknown task', 404

@ns.route('/<task>/<id>')
@ns.response(404, 'Operation not found')
@ns.param('task', 'The specific task')
@ns.param('id', 'The specific task ID')
class PhotosTaskInstances(Resource):

    @ns.doc('get list of task instances')
    def get(self, task, id):
        if is_task(task):
            return [ { "task": f"{task}", "id": f"{id}", "status" : "success"}]
        else:
            return 'unknown task', 404
    
    def put(self, task, id):
        '''create a specific instance of task '''
        # sm = PhotosSyncMgr()
        # result = sm.update_operation(id, ns.payload)
        # return result, 204
        if is_task(task):
            return {'result': f'result-value: {task}', 'id': f"{id}"}

    @ns.doc('delete sync operation')
    @ns.response(204, 'Operation deleted')
    def delete(self, task, id):
        '''Delete an instance of a task given its id'''
        # sm = PhotosSyncMgr()
        # sm.del_operation(id)
        return f'{id}', 204

# @ns.route('/sync-ops')
# class PhotosSyncOperations(Resource):

#     '''Shows all sync operations '''
#     @ns.doc('list sync operations')
#     def get(self):
#         '''List all sync operations '''
#         sm = PhotosSyncMgr()
#         return list(sm.list_operations())

#     @ns.doc('create a sync operation')
#     def post(self):
#         sm = PhotosSyncMgr()
#         # request.data
#         op = request.get_json()
#         return sm.create_sync_operation(operation=op.get('operation','noop'), 
#                                         domain=op.get('domain',None), 
#                                         amount=op.get('amount',0))
    

# @ns.route('/<int:id>')
# @ns.response(404, 'Operation not found')
# @ns.param('id', 'The operation identifier')
# class PhotosSyncOperation(Resource):

#     @ns.doc('get sync operation')
#     def get(self, id):
#         sm = PhotosSyncMgr()
#         op = sm.get_operation(id)
#         if op:
#             return op
#         else:
#             return '', 404
    
#     @ns.doc('delete sync operation')
#     @ns.response(204, 'Operation deleted')
#     def delete(self, id):
#         '''Delete a task given its identifier'''
#         sm = PhotosSyncMgr()
#         sm.del_operation(id)
#         return f'{id}', 204

#     def put(self, id):
#         '''Update a specific operation '''
#         sm = PhotosSyncMgr()
#         result = sm.update_operation(id, ns.payload)
#         return result, 204
