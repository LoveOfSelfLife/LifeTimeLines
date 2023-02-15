from flask_restx import Namespace, Resource, fields, Api
import os
# api = Api(
#     etitle='The APIs',
#     version='1.0',
#     description='THese are some APIs',
# )
# api.add_namespace(ns)

ns = Namespace('mydogs', description='My Dog related operations')


dog = ns.model('Dog', {
    'id': fields.String(required=True, description='The dog identifier'),
    'name': fields.String(required=True, description='The dog name'),
})

DOGS = [
    {'id': 'cole', 'name': 'Colie'},
]

@ns.route('/')
class DogList(Resource):
    @ns.doc('list_dogs')
    @ns.marshal_list_with(dog)
    def get(self):
        '''List all dogs'''
        conn_str = '???'
        c = os.getenv("AZURE_STORAGETABLE_CONNECTIONSTRING")
        if c:
            conn_str = c
        d = DOGS + [{'id': 'cn', 'name' : conn_str}, {'id': 'cn2', 'name' : conn_str}]
        return d

@ns.route('/<id>')
@ns.param('id', 'The dog identifier')
@ns.response(404, 'Dog not found')
class Dog(Resource):
    @ns.doc('get_Dog')
    @ns.marshal_with(dog)
    def get(self, id):
        '''Fetch a dog given its identifier'''
        for d in DOGS:
            if d['id'] == id:
                return d
        ns.abort(404)
