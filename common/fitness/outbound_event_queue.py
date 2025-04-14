import json
import os
import time
from common.env_context import Env
from azure.storage.queue import QueueClient


class OutboundEventQueue:
    OUTBOUND_EVENT_QUEUE_NAME = 'outbound-event-queue'
    TESTING_OUTBOUND_EVENT_QUEUE_NAME = 'testing-outbound-event-queue'
    queue_client = None
    queue_name = None

    @staticmethod
    def get_queue_client():
        if not OutboundEventQueue.queue_client:
            OutboundEventQueue.queue_name = OutboundEventQueue.TESTING_OUTBOUND_EVENT_QUEUE_NAME if Env.ORCH_TESTING_MODE else OutboundEventQueue.OUTBOUND_EVENT_QUEUE_NAME
            OutboundEventQueue.queue_client = QueueClient.from_connection_string(os.getenv("AZURE_STORAGETABLE_CONNECTIONSTRING"), OutboundEventQueue.queue_name)
        return OutboundEventQueue.queue_client
    
