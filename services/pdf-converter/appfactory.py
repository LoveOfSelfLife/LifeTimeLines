import json
import os
import sys
import time
import logging
from azure.storage.queue import QueueClient
from dotenv import load_dotenv
from common.env_context import Env
from common.queue_store import QueueStore
from common.share_client import FShareService
from common.table_store import TableStore
from common.graceful_exit import GracefulExit
from common.auth_requestor import AuthRequestor


class PDF_Converter_Command:
    def __init__(self, message_content_obj, token):
        self.message_content_obj = message_content_obj
        self.token = token

    def covert_to_pdf(self, token):
        # Implement the logic to convert HTML to PDF using the provided token for authentication if needed.
        # This is a placeholder implementation and should be replaced with actual conversion logic.
        logger = logging.getLogger(__name__)
        logger.info(f'Converting HTML to PDF with token')
        # Simulate conversion process
        time.sleep(2)
        logger.info(f'Conversion completed for message: {self.message_content_obj}')
        return True


def main() -> None:

    load_dotenv()
    Env.initialize()

    if Env.AZURE_STORAGETABLE_CONNECTIONSTRING is None:
        raise Exception(f'You attempted to run the container without providing the STORAGE_CONNECTION_STRING')

    if Env.AZURE_FILESHARE_CONNECTIONSTRING is None:
        raise Exception(f'You attempted to run the container without providing the AZURE_FILESHARE_CONNECTION_STRING')

    if Env.AZURE_CLIENT_ID is None:
        raise Exception(f'You attempted to run the container without providing the AZURE_CLIENT_ID')

    if Env.TENANT_ID is None:
        raise Exception(f'You attempted to run the container without providing the TENANT_ID')

    if Env.AZURE_CLIENT_SECRET is None:
        raise Exception(f'You attempted to run the container without providing the AZURE_CLIENT_SECRET')

    TableStore.initialize(Env.AZURE_STORAGETABLE_CONNECTIONSTRING)
    QueueStore.initialize(Env.AZURE_STORAGETABLE_CONNECTIONSTRING)
    FShareService.initialize(Env.AZURE_FILESHARE_CONNECTIONSTRING)

    logging.basicConfig(level=logging.INFO, stream=sys.stdout)  # Adjust level as needed (e.g., DEBUG, INFO, WARNING)
    logger = logging.getLogger(__name__)
    
    queue_client = QueueClient.from_connection_string(os.getenv("AZURE_STORAGETABLE_CONNECTIONSTRING"), 
                                                      "pdf-converter-queue")
    
    logger.info(f'Client created for: pdf-converter-queue')

    exitor = GracefulExit()

    scope = [f"api://{Env.AZURE_CLIENT_ID}/.default"]
    auth = AuthRequestor(Env.TENANT_ID, Env.AZURE_CLIENT_ID, Env.AZURE_CLIENT_SECRET, scope)

    while not exitor.should_exit():

        messages = queue_client.receive_messages()

        logger.info(f'iterate over each message in queue')

        for message in messages:
            logger.info(f'Dequeueing: {message.content}')
            queue_client.delete_message(message.id, message.pop_receipt)
            if message.content is not None:
                message_content_obj = json.loads(message.content)

                cmd = PDF_Converter_Command(message_content_obj, token=auth.get_auth_token())

                try:
                    logger.info(f'START: executing command: {cmd}')

                    result = cmd.covert_to_pdf(token=auth.get_auth_token())

                    logger.info(f'END: executing command: {cmd}')
                except Exception as e:
                    logger.error(f'ERROR: executing command: {cmd}, error: {e}')

            else:
                logger.info(f'no message to process (message.content is empty)')

        logger.info(f'finished iterating over messages, will sleep 5 sec')
        time.sleep(5)
    logger.info(f'exiting container gracefully')
    exit(0)


if __name__ == '__main__':
    main()
