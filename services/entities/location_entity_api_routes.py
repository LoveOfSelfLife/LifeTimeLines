from flask_restx import Namespace, Resource, reqparse, fields
from flask import request, url_for, redirect
import datetime
import json

from common.google_credentials import get_credentials
from common.entities import EntityStore
from common.utils import IDGenerator

class LocationEntity (dict):
    key="id"
    partition="locations"
    fields=["aliases", "name", "city"]
    key_generator=lambda : f"{IDGenerator.gen_id()}"

    def __init__(self, d):
        dict.__init__(d)
        for k,v in d.items():
            self[k] = v


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
        return location_storage.get_list()
    
    @lns.doc('create or update a location entity')
    @lns.expect(lmodel)
    def post(self):
        location_storage = EntityStore(LocationEntity)
        pe = LocationEntity(request.get_json())
        location_storage.upsert_item(pe)
        return { 'id': pe[LocationEntity.key] }, 201

@lns.route('/<id>')
@lns.param('id', 'The location id')
class Person(Resource):
    def get(self, id):
        location_storage = EntityStore(LocationEntity)
        return location_storage.get_item(id)
