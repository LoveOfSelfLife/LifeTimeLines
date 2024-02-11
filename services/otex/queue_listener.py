import json
import os
import time

from azure.storage.queue import QueueClient
from dotenv import load_dotenv
from common.orchestration.orchestration_executor import OrchestrationExecutor
from common.queue_store import QueueStore
from common.table_store import TableStore
from common.graceful_exit import GracefulExit
from common.auth_requestor import AuthRequestor

load_dotenv()


def execute_orchestration(orch_instance_id, steps_to_advance=1, token=None):
    """this method will execute the indicated orchestration intance, by running the indicated task_instances
    the orch_definition defines the details of what needs to be done, the instances are just there to keep track of state
    orch_definition: ID of the orchestration intance, 
    auth token,
    the number of steps to push the orchestration forward.  By default, the orchestration engine will execute the next task that is defined 
    in the orchestration definion, and then it will cede control and post a message for the next task to execute.
    """
    while steps_to_advance > 0:
        executor = OrchestrationExecutor(orch_instance_id, token)
        task_instance = executor.find_next_task_inst_to_run()
        executor.run_task_instance(task_instance)

        steps_to_advance -= 1
    return True
        
def main() -> None:
    print(f'Validate environment variables...')

    STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGETABLE_CONNECTIONSTRING")
    if STORAGE_CONNECTION_STRING is None:
        raise Exception(f'You attempted to run the container without providing the STORAGE_CONNECTION_STRING')

    AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
    if AZURE_CLIENT_ID is None:
        raise Exception(f'You attempted to run the container without providing the AZURE_CLIENT_ID')

    AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
    if AZURE_CLIENT_SECRET is None:
        raise Exception(f'You attempted to run the container without providing the AZURE_CLIENT_SECRET')

    TENANT_ID = os.getenv("TENANT_ID")
    if TENANT_ID is None:
        raise Exception(f'You attempted to run the container without providing the TENANT_ID')

    STORAGE_QUEUE_NAME = 'request-queue'
    if STORAGE_QUEUE_NAME is None:
        raise Exception(f'You attempted to run the container without providing the STORAGE_QUEUE_NAME')

    TableStore.initialize(STORAGE_CONNECTION_STRING)
    QueueStore.initialize(STORAGE_CONNECTION_STRING)

    queue_client = QueueClient.from_connection_string(STORAGE_CONNECTION_STRING, STORAGE_QUEUE_NAME)
    print(f'Client created for: {STORAGE_QUEUE_NAME}')

    exitor = GracefulExit()

    scope = [f"api://{AZURE_CLIENT_ID}/.default"]
    auth = AuthRequestor(TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, scope)

    while not exitor.should_exit():

        messages = queue_client.receive_messages()

        print(f'iterate over each message in queue', flush=True)

        for message in messages:
            print(f'Dequeueing: {message.content}', flush=True)
            queue_client.delete_message(message.id, message.pop_receipt)
            if message.content is not None:
                message_content_obj = json.loads(message.content)
                orch_instance_id = message_content_obj['instanceId']
                steps_to_advance = message_content_obj.get('steps_to_advance', 1)

                result = execute_orchestration(orch_instance_id, steps_to_advance, auth.get_auth_token())

            else:
                print(f'no message to process (message.content is empty)', flush=True)

        print(f'finished iterating over messages, will sleep 5 sec', flush=True)
        time.sleep(5)
    print(f'exiting container gracefully', flush=True)
    exit(0)


if __name__ == '__main__':
    main()
