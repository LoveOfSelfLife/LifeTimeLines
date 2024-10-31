from flask_restx import Namespace, Resource, reqparse, fields
from flask import request, url_for, redirect
import datetime
import json
from common.entity_store import EntityStore
from common.jwt_auth import requires_auth
from common.orchestration.orchestration_utils import OrchestrationCommand, OrchestrationQueue, OrchestrationTaskInstance, OrchestrationDefinition
from common.orchestration.orchestration_utils import  check_if_orch_instance_exists, create_orch_command_instance, create_orch_instances, post_orch_command_instance_to_queue

ns = Namespace('orch', description='orchestration api')

orch_def_resource_fields = ns.model('Resource', {
    'definition': fields.String
})

#TODO: enable requires auth before deploying

@ns.route('/definitions')
class Definitions(Resource):
    ''' '''
    @ns.doc('get definitions')
    # @requires_auth    
    def get(self):
        es = EntityStore()

        res = es.list_items(OrchestrationDefinition())
        return list(res)
    
    @ns.doc('create orchestration definition')
    @ns.expect(orch_def_resource_fields)
    def post(self):
        definition = request.get_json(force=True)
        # definition= json_data['definition']

        if def_id := definition.get('id', None):
            es = EntityStore()
            if es.get_item(OrchestrationDefinition({"id":def_id})):
                return "orch def already exists", 400
            else:
                es.upsert_item(OrchestrationDefinition(definition))

        return "created", 201

@ns.route('/definitions/<id>')
class SingleDefinition(Resource):
    ''' '''
    @ns.doc('get definition')
    # @requires_auth    
    def get(self, id):
        es = EntityStore()
        if odef := es.get_item(OrchestrationDefinition({"id":id})):
            return odef
        else:
            return "not found", 404

orch_instance_resource_fields = ns.model('Resource', {
    'id': fields.String,
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
    @ns.expect(orch_instance_resource_fields)
    # @requires_auth
    def post(self):

        json_data = request.get_json(force=True)
        orch_def_id =json_data['id']
        context = json_data['context']

        es = EntityStore()
        if orch_def := es.get_item(OrchestrationDefinition({"id":orch_def_id})):
            # if it is a valid orch definition, then create an instance, then persist it
            # there will be multiple instances, one for each task
            orch_instances = create_orch_instances(orch_def, context)
            es.upsert_items(orch_instances)
            #
            # then next is to put a message on the message queue to go ahead and execute the orchestration
            # TODO:  post message to execution queue
            #
            return "created", 201
        else:
            return "not found", 404


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

exec_instance_resource_fields = ns.model('Resource', {
    'num_steps': fields.Integer
    })
orch_cmd_resource_fields = ns.model('Resource', {
    'command': fields.String,
    'id': fields.String,
    'arg': fields.Raw
    })

@ns.route('/commands')
class OrchCommandsApi(Resource):
    ''' '''
    @ns.doc('get orchestration command instances')
    # @requires_auth
    def get(self):
        es = EntityStore()
        #if cmd_inst := es.list_items(OrchestrationCommand({"orch_instance_id": orch_instance_id})):
        if cmd_inst := es.list_items(OrchestrationCommand()):
            return list(cmd_inst)
        else:
            return "not found", 404    

    @ns.doc('create execution instance')
    @ns.expect(orch_cmd_resource_fields)
    # @requires_auth
    def post(self):
        OrchestrationQueue.set_testing_mode(True)
        json_data = request.get_json(force=True)
        command =json_data['command']
        orch_instance_id = json_data['id']
        arg = json_data['arg']

        if check_if_orch_instance_exists(orch_instance_id):
            es = EntityStore()
            einst = create_orch_command_instance(command, orch_instance_id, arg)
            es.upsert_item(einst)
            post_orch_command_instance_to_queue(einst)
            return "created", 201
 
        return "orch instance not found", 404
