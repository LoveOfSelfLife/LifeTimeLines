from flask_restx import Namespace, Resource, reqparse, fields
from flask import request, url_for, redirect
import datetime
import json
from common.entities.person import PersonEntity
import logging
from common.google_credentials import get_credentials
from common.entity_store import EntityStore
ns = Namespace('Persons', description='services to define and manage Person Entity metadata')
pmodel = ns.model('Person', {})
logger = logging.getLogger(__name__)
@ns.route('/')
class Persons(Resource):
    ''' '''
    @ns.doc('get list of person entities')
    def get(self):
        person_storage = EntityStore()
        logger.info(f"getting list of persons")
        people =  person_storage.list_items(PersonEntity())
        return list(people)
    
    @ns.doc('create or update a person entity.  The back-end operation is an upsert, so presence of an ID will update an existing entity, and absence of an ID will create a new entity.')
    @ns.expect(pmodel)
    def post(self):
        person_storage = EntityStore()        
        pe = PersonEntity(request.get_json())
        person_storage.upsert_item(pe)
        return { 'id': pe[pe.key_field] }, 201

@ns.route('/<id>')
@ns.param('id', 'person ID')
class Person(Resource):
    @ns.doc('get a specific person entity by ID')
    def get(self, id):
        person_storage = EntityStore()
        it = person_storage.get_item(PersonEntity({"id": id})) 
        if it:
            return it
        else:
            return 'not found', 404

    @ns.doc('delete a person entity by ID')
    def delete(self, id):
        person_storage = EntityStore()
        person_storage.delete([id], PersonEntity)
        return { 'result': id }, 204
    