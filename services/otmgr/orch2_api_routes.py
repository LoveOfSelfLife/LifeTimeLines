from flask_restx import Namespace, Resource, fields
from flask import request
import datetime
import json
from common.entity_store import EntityStore
from common.jwt_auth import requires_auth
from common.orchestration.orchestration_queue import OrchestrationQueue
from common.orchestration.orchestration_utils import OrchestrationCommand, OrchestrationTaskInstance, OrchestrationDefinition
from common.orchestration.orchestration_utils import create_orch2_instances

ns = Namespace('orch2', description='orchestration api V2')

orch2_returned_id= ns.model('Instance_id', {
    "id": fields.String
})    

orch2_instance_resource_fields = ns.model('Orch2_Instance', {
    'orch_definition': fields.Raw,
    "context": fields.Raw
})    


@ns.route('/instances')
class Instances(Resource):
    ''' '''
    @ns.doc('get orchestration instances')
    # @requires_auth
    def get(self):
        es = EntityStore()
        res = es.list_items(OrchestrationTaskInstance())
        return list(res)

    @ns.doc('create orchestration instance')
    @ns.expect(orch2_instance_resource_fields)
    @ns.marshal_with(orch2_returned_id, code=201)
    # @requires_auth
    def post(self):

        json_data = request.get_json(force=True)

        orch2_def = json_data['orch_definition']
        context = json_data['context']

        es = EntityStore()

        # if it is a valid orch definition, then create an instance, then persist it
        # there will be multiple instances, one for each task
        orch2_instances = create_orch2_instances(orch2_def, context)
        es.upsert_items(orch2_instances)

        orch2_instance_id = orch2_instances[0].get('parent_instance_id', None)

        return { "id" : str(orch2_instance_id) }, 201



@ns.route('/instances/<id>')
class SingleInstances(Resource):
    ''' '''
    @ns.doc('get orchestration instance')
    # @requires_auth
    def get(self, id):
        es = EntityStore()
        #if oinst := es.list_items(OrchestrationTaskInstance({"parent_instance_id": id})):
        oi = OrchestrationTaskInstance({"parent_instance_id": id})
        if oinst := es.list_items(oi):
            return list(oinst)
        else:
            return "not found", 404    

