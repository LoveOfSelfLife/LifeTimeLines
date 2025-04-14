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

from common.fitness.outbound_event_queue import OutboundEventQueue
from common.fitness.event_processor import process_event_message

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
    
    outbound_event_queue_client = OutboundEventQueue.get_queue_client()
    logger.info(f'Client created for: {OutboundEventQueue.queue_name}')
    
    exitor = GracefulExit()

    scope = [f"api://{Env.AZURE_CLIENT_ID}/.default"]
    auth = AuthRequestor(Env.TENANT_ID, Env.AZURE_CLIENT_ID, Env.AZURE_CLIENT_SECRET, scope)

    while not exitor.should_exit():

        outbound_event_messages = outbound_event_queue_client.receive_messages()
        for event_message in outbound_event_messages:
            logger.info(f'Dequeueing: {event_message.content}')
            outbound_event_queue_client.delete_message(event_message.id, event_message.pop_receipt)
            if event_message.content is not None:
                event_message_content_obj = json.loads(event_message.content)
                try:
                    logger.info(f'START: processing outbound event message: {event_message_content_obj}')
                    result = process_event_message(event_message_content_obj, auth.get_auth_token())
                    logger.info(f'END: executing outbound event message')
                except Exception as e:
                    logger.error(f'ERROR: processing outbound event message: {e}')
            else:
                logger.info(f'no outbound event message to process (message.content is empty)')

        logger.info(f'finished iterating over messages, will sleep 5 sec')
        time.sleep(5)

    logger.info(f'exiting container gracefully')
    exit(0)

if __name__ == '__main__':
    main()
