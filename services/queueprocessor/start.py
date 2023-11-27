import json
import os

from azure.storage.queue import QueueClient
from dotenv import load_dotenv
from task_processor import execute_task

load_dotenv()

def main() -> None:
    print(f'Validate environment variables...')

    STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGETABLE_CONNECTIONSTRING")
    if STORAGE_CONNECTION_STRING is None:
        raise Exception(f'You attempted to run the container without providing the STORAGE_CONNECTION_STRING')

    STORAGE_QUEUE_NAME = 'request-queue'
    if STORAGE_QUEUE_NAME is None:
        raise Exception(f'You attempted to run the container without providing the STORAGE_QUEUE_NAME')

    assert STORAGE_QUEUE_NAME is not None

    queue_client = QueueClient.from_connection_string(STORAGE_CONNECTION_STRING, STORAGE_QUEUE_NAME)
    print(f'Client created for: {STORAGE_QUEUE_NAME}')

    messages = queue_client.receive_messages()

    m = """
    {
        "service": "test",
        "method": "post",
        "path": "/create-something"
    }
    """

    print(f'now going to iterate over each messages')

    for message in messages:
        print(f'Dequeueing message: {message.content}')
        queue_client.delete_message(message.id, message.pop_receipt)
        if message.content is not None:
            message_content_json = json.loads(message.content)
            task_result = execute_task(message_content_json)
            result_str = json.dumps(task_result, indent=4)
            print(f'got message result: {result_str}')

            msgfile = f'/share/result.json'
            with open(msgfile, 'w') as sf:
                sf.write(result_str)
        else:
            print(f'no message to process (message.content is empty)')

    print(f'finished iterating over messages', flush=True)

    exit(0)


if __name__ == '__main__':
    main()
