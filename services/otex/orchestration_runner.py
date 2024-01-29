
import requests
from common.entity_store import EntityStore
from common.orchestration.orchestration_utils import OrchestrationTaskInstance
from common.orchestration.orchestration_utils import OrchestrationDefinition
# from common.orchestration.orchestration_utils import call_api
import common.orchestration.executors

def advance_orchestration(orch_instance_id, steps_to_advance=1, token=None):

    """this method will execute the indicated orchestration intance.
    args: ID of the orchestration intance, 
    auth token,
    the number of steps to push the orchestration forward.  By default, the orchestration engine will execute the next task that is defined 
    in the orchestration definion, and then it will cede control and post a message for the next task to execute.

    first step is to use the ID of the orchestration intance to hydrate the instance from storage, along with the list of task instances.
    From that we can then hydrate the orchestration definition.
    Each of the retrieved task instances will have a current status. 
    We need to look at the orch definition along with the statuses of the tasks in order to identify the next task that needs to run. 
    
    find_next_task_to_run() can be implemented as follows:
        iterate over all tasks.
        For each task that is not complete, add it and it's dependencies to a directed graph
        run a topological sort on the graph to identify the next task to run

    we need to be careful that we don't fall into an infinite loop here.   One idea is the following:
        each time we try to execute an orchestration instance, we increment a persistent counter on that instance
        then before attempting to execute the instance, we check the counter to verify it hasn't exceeded a threshold

    TODO: Need a test harness for the message queue, to simulate the flow locally.

    Once that task has been identified, we should run it. 
    To tun the task we:
    1. get the task definition from the orchestration template
    2. prepare the inputs to the task by substituting values for any variables defined as part of the input to the task
    3. change the status of the task from "not-stared" to "started" and persist
    4. invoke the function that has been identified as the proxy for the task, passing in the input that was just prepared (step #2)
    5. For simple tasks:
        5.a. wait for the function to complete, and then after it completes, we capture the return value of the function
        5.b. set the output attribute of the task instance to the value returned from the function
        5.c  set the status of the task instance based on the function (if exception through, then status is failed, othewise it is success)
    6. For iterator tasks:
        6.a. we need to invoke the task once for every element in the input iterator. 
        6.b. need to decide if we persist the result after each step in the iteration, or wait till the iteration i scomplete.
            TODO: resolve this open question
        6.c. set the status of the result to something that represents the status from all of the executions of the iteration
    7. then persist the task isntance, and then  proceed as indicated at the top level, which is either to:
        7.a. post the next orchestration request message to the task execution message quewue, or 
        7.b. we should proceed to execute the next task, until the desired number of tasks is done
            
    """
    
    es = EntityStore()
    instances = es.list_items(OrchestrationTaskInstance({"parent_instance_id": orch_instance_id}))
    definition_id = instances[0].get('definition_id')
    definition = None
    if definition_id:
        definition = es.get_item(OrchestrationDefinition({'id': definition_id}))
    next_task = find_next_task_to_exec(definition, instances)
    context = instances['context']
    tasks = instances['tasks']
    
    call_api_fn = getattr(common.orchestration.executors, "call_api")

    service = 'myservice'
    method = 'post'
    path = 'mypath'
    body = 'my-body'
    token = 'my-token'
    
    return call_api_fn(service, method, path, body, token)


def find_next_task_to_exec(definition, instances):
    return None


if __name__ == '__main__':
    print(f'running otex')
    fn = getattr(common.orchestration.executors, "foo")
    fn(3,4,"product")
