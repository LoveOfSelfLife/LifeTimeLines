from flask_restx import Namespace, Resource, reqparse, fields
from flask import request, url_for, redirect
import datetime
import json
from common.entities.person import PersonEntity

from common.google_credentials import get_credentials
from common.entity_store import EntityStore
ns = Namespace('Persons', description='services manage Person Entity metadata')
pmodel = ns.model('Person', {})

@ns.route('/')
class Persons(Resource):
    ''' '''
    @ns.doc('get person entities')
    def get(self):
        headers_str = f"Headers: {request.headers}"
        print(headers_str)
        # storage will return a list of PersonEntity objects
        person_storage = EntityStore()
        # get_list() returns a list of PersonEntity instances, which are just Dicts
        # these will automatically be serialized to JSON by the flask framework
        people =  person_storage.list_items(PersonEntity())
        return list(people)
    
    @ns.doc('create or update a person entity')
    @ns.expect(pmodel)
    def post(self):
        person_storage = EntityStore()        
        pe = PersonEntity(request.get_json())
        person_storage.upsert_item(pe)
        return { 'id': pe[pe.key_field] }, 201

@ns.route('/<ids>')
@ns.param('ids', 'comma-separated list of person ids')
class Person(Resource):
    def get(self, ids):
        person_storage = EntityStore()
        items = [] 
        for id in ids.split(','):
            it = person_storage.get_item(PersonEntity({"id": id})) 
            if it:
                items.append(it)

        if items:
            return items
        else:
            return 'not found', 404

    @ns.doc('delete a person')
    def delete(self, ids):
        person_storage = EntityStore()
        id_list = ids.split(',')
        person_storage.delete(id_list, PersonEntity)
        return { 'result': id_list }, 204
    