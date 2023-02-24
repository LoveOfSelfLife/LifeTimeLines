from flask_restx import Namespace, Resource, fields
from flask import request
from werkzeug.utils import secure_filename
import os

ns = Namespace('feapp', description='Front-end app operations')

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
DAO.create({'task': 'Build an API'})
DAO.create({'task': '?????'})
DAO.create({'task': 'profit!'})


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

