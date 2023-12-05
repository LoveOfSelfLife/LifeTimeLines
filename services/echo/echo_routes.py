from flask_restx import Namespace, Resource, reqparse, fields
from flask import request, url_for, redirect
import datetime
import json

pns = Namespace('echos', description='echo api')

@pns.route('/')
class Persons(Resource):
    ''' '''
    @pns.doc('echo')
    def get(self):
        headers_str = f"Headers: {request.headers}"
        print(headers_str)
        # storage will return a list of PersonEntity objects
        person_storage = EntityStore(PersonEntity)
        # get_list() returns a list of PersonEntity instances, which are just Dicts
        # these will automatically be serialized to JSON by the flask framework
        people =  person_storage.list_items()
        return list(people)
    
    @pns.doc('create or update a person entity')
    @pns.expect(pmodel)
    def post(self):
        person_storage = EntityStore(PersonEntity)        
        pe = PersonEntity(request.get_json())
        person_storage.upsert_item(pe)
        return { 'id': pe[pe.key_field] }, 201

@pns.route('/<ids>')
@pns.param('ids', 'comma-separated list of person ids')
class Person(Resource):
    def get(self, ids):
        person_storage = EntityStore(PersonEntity)
        return [ person_storage.get_item(id) for id in ids.split(',') ]

    @pns.doc('delete a person')
    def delete(self, ids):
        person_storage = EntityStore(PersonEntity)        
        id_list = ids.split(',')
        person_storage.delete(id_list)
        return { 'result': id_list }, 204
    