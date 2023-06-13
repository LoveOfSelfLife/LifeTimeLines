from flask_restx import Namespace, Resource, reqparse, fields
from flask import request, url_for, redirect
import datetime
import json

from common.google_credentials import get_credentials
from common.entities import PersonEntity, PersonEntityStore
ns = Namespace('entities', description='services manage entity metadata')
pmodel = ns.model('Person', {})

@ns.route('/persons')
class Persons(Resource):
    ''' '''
    @ns.doc('get person entities')
    def get(self):
        # storage will return a list of PersonEntity objects
        person_storage = PersonEntityStore()
        # get_list() returns a list of PersonEntity instances, which are just Dicts
        # these will automatically be serialized to JSON by the flask framework
        return person_storage.get_list()
    
    @ns.doc('create or update a person entity')
    @ns.expect(pmodel)
    def post(self):
        person_storage = PersonEntityStore()
        pe = PersonEntity(request.get_json())
        person_storage.upsert_item(pe)
        return { 'id': pe.get_row_key() }, 201

@ns.route('/persons/<id>')
@ns.param('id', 'The person id')
class Person(Resource):
    def get(self, id):
        person_storage = PersonEntityStore()
        return person_storage.get_item(id)
