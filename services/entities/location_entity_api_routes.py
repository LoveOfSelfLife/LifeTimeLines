from flask_restx import Namespace, Resource, reqparse, fields
from flask import request, url_for, redirect
import datetime
import json

from common.google_credentials import get_credentials
from common.entity_store import EntityStore
from common.entities.location import LocationEntity

ns = Namespace('Locations', description='services to manage location entities')
lmodel = ns.model('Location', {})

@ns.route('/')
class Locations(Resource):
    ''' '''
    @ns.doc('get location entities')
    def get(self):
        # storage will return a list of PersonEntity objects
        location_storage = EntityStore()
        # get_list() returns a list of PersonEntity instances, which are just Dicts
        # these will automatically be serialized to JSON by the flask framework
        return list(location_storage.list_items(LocationEntity()))
    
    @ns.doc('create or update a location entity')
    @ns.expect(lmodel)
    def post(self):
        location_storage = EntityStore()
        pe = LocationEntity(request.get_json())
        location_storage.upsert_item(pe)
        return { 'id': pe[pe.key_field] }, 201

@ns.route('/<ids>')
@ns.param('ids', 'comma separated list of IDs')
class Location(Resource):
    def get(self, ids):
        location_storage = EntityStore()
        items = [] 
        for id in ids.split(','):
            it = location_storage.get_item(LocationEntity({"id": id})) 
            if it:
                items.append(it)
        if items:
            return items
        else:
            return 'not found', 404

    @ns.doc('delete locations')
    def delete(self, ids):
        location_storage = EntityStore()
        id_list = ids.split(',')
        location_storage.delete(id_list, LocationEntity)
        return { 'result': id_list }, 204

