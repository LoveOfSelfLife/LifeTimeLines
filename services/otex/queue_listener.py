import json
import os
import time

from azure.storage.queue import QueueClient
from dotenv import load_dotenv
from common.queue_store import QueueStore
from common.table_store import TableStore
from common.graceful_exit import GracefulExit
from common.auth_requestor import AuthRequestor
from common.orchestration.orchestration_utils import OrchestrationCommand, OrchestrationQueue
from common.orchestration.orchestration_executor import execute_orchestration

load_dotenv()

    # steps_to_advance = int(arg) if arg else 1
    # while steps_to_advance > 0:
    #     executor = OrchestrationExecutor(orch_data, orch_instance_id, token)
    #     task_instance = executor.find_next_task_inst_to_run()
    #     if task_instance is None:
    #         return False
    #     executor.run_task_instance(task_instance)
    #     steps_to_advance -= 1
    # return True


        
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

    ORCH_TESTING_MODE = os.getenv("ORCH_TESTING_MODE")
    if ORCH_TESTING_MODE:
        OrchestrationQueue.set_testing_mode(True)

    TableStore.initialize(STORAGE_CONNECTION_STRING)
    QueueStore.initialize(STORAGE_CONNECTION_STRING)

    queue_client = OrchestrationQueue.get_queue_client()
    print(f'Client created for: {OrchestrationQueue.queue_name}')

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
                orch_cmd = OrchestrationCommand(message_content_obj)

                result = execute_orchestration(orch_cmd=orch_cmd, token=auth.get_auth_token())

            else:
                print(f'no message to process (message.content is empty)', flush=True)

        print(f'finished iterating over messages, will sleep 5 sec', flush=True)
        time.sleep(5)
    print(f'exiting container gracefully', flush=True)
    exit(0)


if __name__ == '__main__':
    main()
