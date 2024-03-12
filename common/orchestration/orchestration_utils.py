import json
import os
import time
import requests
from common.entity_store import EntityObject, EntityStore
from azure.storage.queue import QueueClient
import common.orchestration.modules.executors

class OrchestrationQueue:
    STORAGE_QUEUE_NAME = 'request-queue'
    TESTING_STORAGE_QUEUE_NAME = 'testing-queue'
    queue_client = None
    queue_name = STORAGE_QUEUE_NAME

    @staticmethod
    def get_queue_client():
        if OrchestrationQueue.queue_client:
            return OrchestrationQueue.queue_client
        else:
            OrchestrationQueue.queue_client = QueueClient.from_connection_string(os.getenv("AZURE_STORAGETABLE_CONNECTIONSTRING"), OrchestrationQueue.queue_name)
            return OrchestrationQueue.queue_client
    
    @staticmethod
    def set_testing_mode(testing_mode=False):
        if testing_mode:
            OrchestrationQueue.queue_name = OrchestrationQueue.TESTING_STORAGE_QUEUE_NAME
        else:
            OrchestrationQueue.queue_name = OrchestrationQueue.STORAGE_QUEUE_NAME

    
class OrchestrationDefinition (EntityObject):
    """ this table 
    """
    table_name='OrchestrationDefTable'
    fields=["id", "version", "context", "tasks", "flow"]
    key_field="id"
    partition_value="orch_def"

    def __init__(self, d={}):
        super().__init__(d)

class OrchestrationCommand (EntityObject):
    """ this table 
    """
    table_name='OrchestrationCommandTable'
    fields=["id", "command", "orch_instance_id", "arg", "status"]

    key_field="id"
    partition_field="orch_instance_id"

    def __init__(self, d={}):
        super().__init__(d)

class OrchestrationTaskInstance (EntityObject):
    """ this table 
    """
    table_name='OrchestrationInstanceTable'
    fields=["id", "parent_instance_id", "status", "child_tasks", 
            "task_id", "execution_details", "executions", "definition_id", 
            "context", "task", "is_parent", "output", "step_status", "exec_index"]
    key_field="id"
    partition_field="parent_instance_id"

    def __init__(self, d={}):
        super().__init__(d)

class AbstratctOrchDataStore:
    def get_orch_data(self, id):
        pass
    def persist_instance(self, instance):
        pass

class OrchTaskDefDataStore (AbstratctOrchDataStore):
    def __init__(self):
        self.es = EntityStore()

    def get_orch_data(self, orch_instance_id):
        instances = list(self.es.list_items(OrchestrationTaskInstance({"parent_instance_id": orch_instance_id})))
        instance = None
        tasks = []
        for inst in instances:
            if inst.get('is_parent', None):
                instance = inst
            else:
                tasks.append(inst)

        definition_id = instance.get('definition_id', None)

        if definition_id:
            definition = self.es.get_item(OrchestrationDefinition({'id': definition_id}))

        return definition, instance, tasks

    def persist_instance(self, instance):
        self.es.upsert_item(instance)

def create_orch_instances(definition, context):
    # need to create unique IDs for the parent instance, as well as for each of the child tasks
    # if an orchestration has 3 tasks, then this will create 4 records
    # the first record is for the orchestration instance itself, which is considered the parent record
    # the ID (RowKey) of that record will be the orchestration instance ID
    # As there are 3 tasks defined for this orchestration, there will also be 3 records, one for each task
    # the ID (RowKey) of each of those task records will be the unique task ID, which will be the instance ID appended with a unique int
    # the PartionKey for all 4 records will be the parent orchestration instance ID, which is used to tie all of these records together

    # the context is attached to the parent instance record
    instance_records = []
    i = 0
    definition_id = definition['id']
    parent_instance_id = str(int(time.time())) # just use the current second since the beginning of unix time as the instance id
    child_tasks = {}

    for task_def in definition.get('tasks', []):
        task_instance_id = f"{parent_instance_id}-{i}"
        instance_records.append(OrchestrationTaskInstance({"id": task_instance_id,
                                                        "parent_instance_id": parent_instance_id,
                                                        "status": "not_started",
                                                        "task_id": task_def.get('taskId',None),
                                                        "definition_id": definition_id,
                                                        "context": None,
                                                        "is_parent": False,
                                                        "output" : None,
                                                        "execution_details" : [],
                                                        "executions" : [],
                                                        "exec_index" : 0
                                                        }))
        child_tasks[task_def['taskId']] = task_instance_id
        i += 1

    # prepend the orch instance to the front of the returned list
    instance_records.insert(0, OrchestrationTaskInstance({"id": f"{parent_instance_id}", 
                                                            "parent_instance_id": f"{parent_instance_id}",
                                                            "status": "not_started",
                                                            "context": context,
                                                            "definition_id": definition_id,
                                                            "child_tasks": child_tasks,
                                                            "is_parent": True,
                                                            "output" : None
                                                            }))
    return instance_records

def check_if_orch_instance_exists(orch_instance_id):
    es =EntityStore()
    return es.get_item(OrchestrationTaskInstance({"parent_instance_id": orch_instance_id, "id": orch_instance_id}))

def create_orch_command_instance(command, orch_instance_id, arg):

    cmd_instance_id = str(int(time.time())) # just use the current second since the beginning of unix time as the instance id

    cmd_instance = OrchestrationCommand({"id": f"{cmd_instance_id}", 
                                        "orch_instance_id": f"{orch_instance_id}",
                                        "command": command,
                                        "arg": arg,
                                        "status": "initial"})
    return cmd_instance

def post_orch_command_instance_to_queue(orch_cmd_inst:OrchestrationCommand):
    queue_client = OrchestrationQueue.get_queue_client()
    exec_instance_str = json.dumps(orch_cmd_inst)
    queue_client.send_message(exec_instance_str)

def get_orchestration_instances(orch_instance_id):
    es = EntityStore()
    instances = list(es.list_items(OrchestrationTaskInstance({"parent_instance_id": orch_instance_id})))
    instance = None
    tasks = []
    for inst in instances:
        if inst.get('is_parent', None):
            isntance = inst
        else:
            tasks.append(inst)

    definition_id = instance.get('definition_id', None)

    if definition_id:
        definition = es.get_item(OrchestrationDefinition({'id': definition_id}))

    return definition, instance, tasks
