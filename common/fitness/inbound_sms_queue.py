import json
import os
import time
from common.env_context import Env
from azure.storage.queue import QueueClient


class InboundSMSQueue:
    INBOUND_SMS_QUEUE_NAME = 'inbound-sms-queue'
    TESTING_INBOUND_SMS_QUEUE_NAME = 'inbound-sms-queue'
    # TESTING_INBOUND_SMS_QUEUE_NAME = 'testing-inbound-sms-queue'

    queue_client = None
    queue_name = None

    @staticmethod
    def get_queue_client():
        if not InboundSMSQueue.queue_client:
            InboundSMSQueue.queue_name = InboundSMSQueue.TESTING_INBOUND_SMS_QUEUE_NAME if Env.ORCH_TESTING_MODE else InboundSMSQueue.INBOUND_SMS_QUEUE_NAME
            InboundSMSQueue.queue_client = QueueClient.from_connection_string(os.getenv("AZURE_STORAGETABLE_CONNECTIONSTRING"), InboundSMSQueue.queue_name)
        return InboundSMSQueue.queue_client
    
