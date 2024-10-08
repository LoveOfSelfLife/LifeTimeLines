from flask_restx import Namespace, Resource, fields
from flask import request
from werkzeug.utils import secure_filename
import os
# from aztables import SampleTablesQuery
import requests

ns = Namespace('feapp', description='Front-end app operations', path='/fe')

todo = ns.model('fe', {
    'id': fields.Integer(readonly=True, description='The task unique identifier'),
    'task': fields.String(required=True, description='The task details')
})

class TodoDAO(object):
    def __init__(self):
        self.counter = 0
        self.todos = []

    def get(self, id):
        for td in self.todos:
            if td['id'] == id:
                return td
        ns.abort(404, "Todo {} doesn't exist".format(id))

    def create(self, data):
        td = data
        td['id'] = self.counter = self.counter + 1
        self.todos.append(td)
        return td

    def update(self, id, data):
        td = self.get(id)
        td.update(data)
        return td

    def delete(self, id):
        td = self.get(id)
        self.todos.remove(td)


DAO = TodoDAO()
DAO.create({'task': 'This is the latest feapp, now up to feapp4'})
DAO.create({'task': '?????'})
DAO.create({'task': 'profit!'})
DAO.create({'task': 'this'})
DAO.create({'task': 'is'})
DAO.create({'task': 'new'})
DAO.create({'task': 'to verify the push to azure'})


@ns.route('/')
class TodoList(Resource):
    '''Shows a list of all todos, and lets you POST to add new tasks'''
    @ns.doc('list_todos')
    @ns.marshal_list_with(todo)
    def get(self):
        '''List all tasks'''
        return DAO.todos
 
    @ns.doc('create by posting a file')
    @ns.marshal_with(todo)
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

    # def post(self):
    #     with open("/tmp/flask-stream-demo", "bw") as f:
    #         chunk_size = 4096
    #         while True:
    #             chunk = request.stream.read(chunk_size)
    #             if len(chunk) == 0:
    #                 return
    #             f.write(chunk)

@ns.route('/<int:id>')
@ns.response(404, 'Todo not found')
@ns.param('id', 'The task identifier')
class Todo(Resource):
    '''Show a single todo item and lets you delete them'''
    @ns.doc('get_todo')
    @ns.marshal_with(todo)
    def get(self, id):
        '''Fetch a given resource'''
        return DAO.get(id)

    @ns.doc('delete_todo')
    @ns.response(204, 'Todo deleted')
    def delete(self, id):
        '''Delete a task given its identifier'''
        DAO.delete(id)
        return '', 204

    @ns.expect(todo)
    @ns.marshal_with(todo)
    def put(self, id):
        '''Update a task given its identifier'''
        return DAO.update(id, ns.payload)


@ns.route('/solr')
class Solr(Resource):
    '''proxy requests to the back-end SOLR instance'''
    @ns.doc('solr get')
    def get(self):
        SOLR_URL='http://wgt.ltl.richkempinski.com/solr/wgt_core/select?indent=true&q.op=OR&q=*%3A*&useParams='
        resp = requests.get(SOLR_URL, verify=False)
        return resp.json()
        
    @ns.doc('post to solr')
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

@ns.route('/headers')
class Headers(Resource):
    '''return the headers'''
    @ns.doc('show headers')
    def get(self):
        '''return headers'''
        h = { k:v for k,v in request.headers.items() }
        return h
