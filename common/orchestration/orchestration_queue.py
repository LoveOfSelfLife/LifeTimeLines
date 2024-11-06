import json
import os
import time
from common.env_context import Env
from azure.storage.queue import QueueClient


class OrchestrationQueue:
    STORAGE_QUEUE_NAME = 'request-queue'
    TESTING_STORAGE_QUEUE_NAME = 'testing-queue'
    queue_client = None
    queue_name = None

    @staticmethod
    def get_queue_client():
        if not OrchestrationQueue.queue_client:
            OrchestrationQueue.queue_name = OrchestrationQueue.TESTING_STORAGE_QUEUE_NAME if Env.ORCH_TESTING_MODE else OrchestrationQueue.STORAGE_QUEUE_NAME
            OrchestrationQueue.queue_client = QueueClient.from_connection_string(os.getenv("AZURE_STORAGETABLE_CONNECTIONSTRING"), OrchestrationQueue.queue_name)
        return OrchestrationQueue.queue_client
    
