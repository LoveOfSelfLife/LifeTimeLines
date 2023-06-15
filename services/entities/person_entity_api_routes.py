from flask_restx import Namespace, Resource, reqparse, fields
from flask import request, url_for, redirect
import datetime
import json

from common.google_credentials import get_credentials
from common.entities import PersonEntity, EntityStore
pns = Namespace('persons', description='services manage entity metadata')
pmodel = pns.model('Person', {})

@pns.route('/')
class Persons(Resource):
    ''' '''
    @pns.doc('get person entities')
    def get(self):
        # storage will return a list of PersonEntity objects
        person_storage = EntityStore(PersonEntity)
        # get_list() returns a list of PersonEntity instances, which are just Dicts
        # these will automatically be serialized to JSON by the flask framework
        return person_storage.get_list()
    
    @pns.doc('create or update a person entity')
    @pns.expect(pmodel)
    def post(self):
        person_storage = EntityStore(PersonEntity)        
        pe = PersonEntity(request.get_json())
        person_storage.upsert_item(pe)
        return { 'id': pe[pe.key] }, 201

@pns.route('/<id>')
@pns.param('id', 'The person id')
class Person(Resource):
    def get(self, id):
        person_storage = EntityStore(PersonEntity)
        return person_storage.get_item(id)

