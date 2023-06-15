from flask_restx import Namespace, Resource, reqparse, fields
from flask import request, url_for, redirect
import datetime
import json

from common.google_credentials import get_credentials
from common.entities import PersonEntity, EntityStore

lns = Namespace('Other', description='services to manage other entities')
lmodel = lns.model('Location', {})

@lns.route('/')
class Locations(Resource):
    ''' '''
    @lns.doc('get location entities')
    def get(self):
        # storage will return a list of PersonEntity objects
        person_storage = EntityStore(PersonEntity)
        # get_list() returns a list of PersonEntity instances, which are just Dicts
        # these will automatically be serialized to JSON by the flask framework
        return person_storage.get_list()
    
    @lns.doc('create or update a location entity')
    @lns.expect(lmodel)
    def post(self):
        person_storage = EntityStore(PersonEntity)
        pe = PersonEntity(request.get_json())
        person_storage.upsert_item(pe)
        return { 'id': pe.get_row_key() }, 201

@lns.route('/<id>')
@lns.param('id', 'The location id')
class Person(Resource):
    def get(self, id):
        person_storage = EntityStore(PersonEntity)
        return person_storage.get_item(id)
