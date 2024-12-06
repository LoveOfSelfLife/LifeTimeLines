from flask_restx import Namespace, Resource, reqparse, fields
from flask import request, url_for, redirect
import datetime
import json

from common.google_credentials import get_credentials
from common.entity_store import EntityStore
from common.configs import DriveSyncConfig
from common.entities.location import LocationEntity
from common.entities.person import PersonEntity
from common.entities.entity_registry import EntityRegistry

ns = Namespace('generic', description='generic services to manage generic entities')
lmodel = ns.model('Generic', {})

parser = reqparse.RequestParser()
parser.add_argument('entity-type', type=str, help='entity type')

entities_map = EntityRegistry.editable_entities

def get_entity_type(entity_type_id):
    return entities_map.get(entity_type_id, None)

@ns.route('/')
class Generic(Resource):    

    @ns.doc('get the generic entities')
    @ns.expect(parser)
    def get(self):
        entity_type_id = request.args.get('entity-type')
        if not entity_type_id:
            return "No entity type id provided", 404

        es = EntityStore()
        entity_type = get_entity_type(entity_type_id)
        if entity_type is None:
            return "Entity type not found", 404
        return list(es.list_items(entity_type))

    @ns.doc('create or update a generic entity')
    @ns.expect(lmodel, parser)
    def post(self):
        entity_type_id = request.args.get('entity-type')
        if not entity_type_id:
            return "No entity type id provided", 404

        es = EntityStore()
        entity_type = get_entity_type(entity_type_id)

        if entity_type is None:
            return "Entity type not found", 404
        entity_class = entity_type.__class__
        ge = entity_class(request.get_json())
        es.upsert_item(ge)
        return { 'id': ge[ge.key_field] }, 201

# @ns.route('/<ids>')
# @ns.param('ids', 'comma separated list of IDs')
# class Location(Resource):
#     def get(self, ids):
#         location_storage = EntityStore()
#         items = [] 
#         for id in ids.split(','):
#             it = location_storage.get_item(LocationEntity({"id": id})) 
#             if it:
#                 items.append(it)
#         if items:
#             return items
#         else:
#             return 'not found', 404

    # @ns.doc('delete locations')
    # def delete(self, ids):
    #     location_storage = EntityStore()
    #     id_list = ids.split(',')
    #     location_storage.delete(id_list, LocationEntity)
    #     return { 'result': id_list }, 204

