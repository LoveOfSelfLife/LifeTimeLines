import json
import os
import time
import msal

from azure.storage.queue import QueueClient
from dotenv import load_dotenv
from task_processor import execute_task
from common.graceful_exit import GracefulExit

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

    assert STORAGE_QUEUE_NAME is not None

    queue_client = QueueClient.from_connection_string(STORAGE_CONNECTION_STRING, STORAGE_QUEUE_NAME)
    print(f'Client created for: {STORAGE_QUEUE_NAME}')

    exitor = GracefulExit()

    config= {
        "authority": f"https://login.microsoftonline.com/{TENANT_ID}",
        "client_id": AZURE_CLIENT_ID,
        "scope": ["api://5b6214a0-1564-4c7e-ad9f-21cb50f78a6a/.default"],
            #  For more information about scopes for an app, refer:
            #  https://docs.microsoft.com/en-us/azure/active-directory/develop/v2-oauth2-client-creds-grant-flow#second-case-access-token-request-with-a-certificate"
        "secret": AZURE_CLIENT_SECRET
            #  For information about generating client secret, refer:
            #  https://github.com/AzureAD/microsoft-authentication-library-for-python/wiki/Client-Credentials#registering-client-secrets-using-the-application-registration-portal
    }

    # Create a preferably long-lived app instance which maintains a token cache.
    app = msal.ConfidentialClientApplication(
        config["client_id"], 
        authority=config["authority"],
        client_credential=config["secret"],
        # token_cache=...  # Default cache is in memory only.
        )

    result = app.acquire_token_silent(config["scope"], account=None)
    if not result:
        print("No suitable token exists in cache. Let's get a new one from AAD.")
        result = app.acquire_token_for_client(scopes=config["scope"])    

    if "access_token" in result:
        # Calling graph using the access token
        token = result['access_token']
    else:
        print(result.get("error"))
        print(result.get("error_description"))
        print(result.get("correlation_id"))  # You may need this when reporting a bug
        raise Exception(f'cannot get auth token')

    while not exitor.should_exit():

        messages = queue_client.receive_messages()

        """
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
                task_result = execute_task(message_content_json, token)
                print(f'received result from execute_task: {task_result}')
                result_str = task_result
                # result_str = json.dumps(task_result, indent=4)
                print(f'got message result: {result_str}')

                msgfile = f'/share/result.json'
                with open(msgfile, 'w') as sf:
                    sf.write(result_str)
            else:
                print(f'no message to process (message.content is empty)')

        print(f'finished iterating over messages, will sleep now', flush=True)
        time.sleep(5)
    
    print(f'exiting container gracefully', flush=True)

    exit(0)


if __name__ == '__main__':
    main()
