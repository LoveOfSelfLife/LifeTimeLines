import json
import os
import time

from azure.storage.queue import QueueClient
from dotenv import load_dotenv
from task_processor import execute_task
from common.graceful_exit import GracefulExit
from common.auth_requestor import AuthRequestor

load_dotenv()
        
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

    # assert STORAGE_QUEUE_NAME is not None

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
                message_content_json = json.loads(message.content)
                task_result = execute_task(message_content_json, auth.get_auth_token())
                print(f'received result from execute_task: {task_result}', flush=True)
                result_str = task_result

                msgfile = f'/share/result.json'
                with open(msgfile, 'a') as sf:
                    sf.write(result_str)
            else:
                print(f'no message to process (message.content is empty)', flush=True)

        print(f'finished iterating over messages, will sleep 5 sec', flush=True)
        time.sleep(5)
    print(f'exiting container gracefully', flush=True)
    exit(0)


if __name__ == '__main__':
    main()
