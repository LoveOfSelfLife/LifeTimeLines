from flask_restx import Namespace, Resource, fields


ns = Namespace('mycats', description='My Cat related operations')


cat = ns.model('Cat', {
    'id': fields.String(required=True, description='The cat identifier'),
    'name': fields.String(required=True, description='The cat name'),
})

CATS = [
    {'id': 'felix', 'name': 'Felix'},
]

@ns.route('/')
class CatList(Resource):
    @ns.doc('list_cats')
    @ns.marshal_list_with(cat)
    def get(self):
        '''List all cats'''
        return CATS

@ns.route('/<id>')
@ns.param('id', 'The cat identifier')
@ns.response(404, 'Cat not found')
class Cat(Resource):
    @ns.doc('get_cat')
    @ns.marshal_with(cat)
    def get(self, id):
        '''Fetch a cat given its identifier'''
        for cat in CATS:
            if cat['id'] == id:
                return cat
        ns.abort(404)
