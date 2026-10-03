import json
import os
import time
from azure.storage.queue import QueueClient


class OutboundEventQueue:
    OUTBOUND_EVENT_QUEUE_NAME = 'outbound-event-queue'
    TESTING_OUTBOUND_EVENT_QUEUE_NAME = 'testing-outbound-event-queue'
    queue_client = None
    queue_name = None

    @staticmethod
    def get_queue_client(connection_string=None):
        if connection_string is None:
            connection_string = os.getenv("AZURE_STORAGETABLE_CONNECTIONSTRING")
        if not OutboundEventQueue.queue_client:
            OutboundEventQueue.queue_name = OutboundEventQueue.TESTING_OUTBOUND_EVENT_QUEUE_NAME if os.getenv("ORCH_TESTING_MODE") else OutboundEventQueue.OUTBOUND_EVENT_QUEUE_NAME
            OutboundEventQueue.queue_client = QueueClient.from_connection_string(connection_string, OutboundEventQueue.queue_name)
        return OutboundEventQueue.queue_client
    
