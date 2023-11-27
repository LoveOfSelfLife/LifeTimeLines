from flask_restx import Namespace, Resource, reqparse, fields
from flask import request, url_for, redirect
import datetime
import json

from common.google_credentials import get_credentials
from common.entity_store import EntityStore
from common.entities.location import LocationEntity

lns = Namespace('Locations', description='services to manage location entities')
lmodel = lns.model('Location', {})

@lns.route('/')
class Locations(Resource):
    ''' '''
    @lns.doc('get location entities')
    def get(self):
        # storage will return a list of PersonEntity objects
        location_storage = EntityStore(LocationEntity)
        # get_list() returns a list of PersonEntity instances, which are just Dicts
        # these will automatically be serialized to JSON by the flask framework
        return list(location_storage.list_items())
    
    @lns.doc('create or update a location entity')
    @lns.expect(lmodel)
    def post(self):
        location_storage = EntityStore(LocationEntity)
        pe = LocationEntity(request.get_json())
        location_storage.upsert_item(pe)
        return { 'id': pe[LocationEntity.key_field] }, 201

@lns.route('/<id>')
@lns.param('id', 'The location id')
class Person(Resource):
    def get(self, id):
        location_storage = EntityStore(LocationEntity)
        return location_storage.get_item(id)

