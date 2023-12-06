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
        location_storage = EntityStore(LocationEntity)
        # get_list() returns a list of PersonEntity instances, which are just Dicts
        # these will automatically be serialized to JSON by the flask framework
        return list(location_storage.list_items())
    
    @ns.doc('create or update a location entity')
    @ns.expect(lmodel)
    def post(self):
        location_storage = EntityStore(LocationEntity)
        pe = LocationEntity(request.get_json())
        location_storage.upsert_item(pe)
        return { 'id': pe[LocationEntity.key_field] }, 201

@ns.route('/<id>')
@ns.param('id', 'The location id')
class Person(Resource):
    def get(self, id):
        location_storage = EntityStore(LocationEntity)
        return location_storage.get_item(id)

