import time
import requests
from common.entity_store import EntityObject
import common.orchestration.executors

class OrchestrationDefinition (EntityObject):
    """ this table 
    """
    table_name='OrchestrationDefTable'
    fields=["id", "version", "context", "tasks", "iterator"]
    key_field="id"
    partition_value="orch_def"

    def __init__(self, d={}):
        super().__init__(d)

class OrchestrationTaskInstance (EntityObject):
    """ this table 
    """
    table_name='OrchestrationInstanceTable'
    fields=["id", "parent_instance_id", "child_tasks", "definition_id", "context", "task", "status", "is_parent", "output", "iterator"]
    key_field="id"
    partition_field="parent_instance_id"

    def __init__(self, d={}):
        super().__init__(d)

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
        iterator_task = task_def.get('iterator', None)
        instance_records.append(OrchestrationTaskInstance({"id": task_instance_id,
                                                        "parent_instance_id": parent_instance_id,
                                                        "status": "not_started",
                                                        "definition_id": definition_id,                                                        
                                                        "context": None,
                                                        "is_parent": False,
                                                        "output" : None,
                                                        "iterator": iterator_task
                                                        }))
        child_tasks[task_def['id']] = task_instance_id
        i += 1

    instance_records.append(OrchestrationTaskInstance({"id": f"{parent_instance_id}", 
                                                            "parent_instance_id": f"{parent_instance_id}",
                                                            "status": "not_started",
                                                            "context": context,
                                                            "definition_id": definition_id,
                                                            "child_tasks": child_tasks,
                                                            "is_parent": True,
                                                            "output" : None
                                                            }))
    return instance_records

