import copy
import time
import requests
from common.entity_store import EntityObject, EntityStore
import common.orchestration.executors
import json

class OrchestrationDefinition (EntityObject):
    """ this table 
    """
    table_name='OrchestrationDefTable'
    fields=["id", "version", "context", "tasks", "flow"]
    key_field="id"
    partition_value="orch_def"

    def __init__(self, d={}):
        super().__init__(d)

class OrchestrationTaskInstance (EntityObject):
    """ this table 
    """
    table_name='OrchestrationInstanceTable'
    fields=["id", "parent_instance_id", "status", "child_tasks", 
            "task_id", "execution_details", "executions", "definition_id", 
            "context", "task", "is_parent", "output"]
    key_field="id"
    partition_field="parent_instance_id"

    def __init__(self, d={}):
        super().__init__(d)

class AbstratctOrchStore:
    def get_orch_data(self, id):
        pass
    def persist_instance(self, instance):
        pass

class OrchTaskDefStore (AbstratctOrchStore):
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

class TestingStore (AbstratctOrchStore):
    def __init__(self, definition, orch_instance, task_instances):
        self.es = EntityStore()
        self.definition = definition
        self.orch_instance = [ orch_instance ]
        self.task_instances = {}
        for task in task_instances:
            self.task_instances[task['task_id']] = [ task ]

    def get_orch_data(self, orch_instance_id):
        return self.definition, copy.deepcopy(self.orch_instance[-1]), [ copy.deepcopy(t[-1]) for t in self.task_instances.values()]
    
    def persist_instance(self, instance):
        if instance['is_parent']:
            self.orch_instance.append(instance)
        else:
            self.task_instances[instance['task_id']].append(instance)

    def get_all_orch_data(self, orch_instance_id):
        return self.definition, self.orch_instance, [ t for t in self.task_instances.values()]

    def __str__(self):
        d,o,t = self.get_orch_data(self, None)
        d,o_all,t_all = self.get_all_orch_data(self, None)

        return json.dumps({"latest" : { "instances" :  o,
                                        "tasks" : t},
                            "all": { "instances" :  o_all,
                                    "tasks" : t_all},
                }, indent=4)


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


def create_task_input_dict(task_instance_id, orch_def, orch_instance):
    """analysze the fields defined in the input structure of the task instance,
    replace all variables with values from the context & from the tasks

    Args:
        task_instance_id (_type_): _description_
        orch_def (_type_): _description_
        orch_instance (_type_): _description_
    """
    pass
