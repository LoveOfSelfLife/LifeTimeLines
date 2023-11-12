
from azure.core.exceptions import ResourceExistsError
from azure.storage.queue import QueueClient, QueueMessage

class QueueStore():
    connection_string = None

    @staticmethod
    def initialize(connection_string):
        QueueStore.connection_string = connection_string

    def __init__(self, queue_name:str):
        if not self.connection_string:
            raise Exception("Table connection creds null")
        self.queue_client = QueueClient.from_connection_string(conn_str=QueueStore.connection_string, queue_name=queue_name)
        try:
            self.queue_client.create_queue()
            print(f"Created queue: {queue_name}")
        except ResourceExistsError:
            print(f"Queue {queue_name} already exists")

    def enque_msg(self, msg:str):
        self.queue_client.send_message(msg)

    def deque_msg(self):
        msg: QueueMessage = self.queue_client.receive_message()
        if msg:
            content = msg.content
            self.queue_client.delete_message(msg)
            return content
        else:
            return None

