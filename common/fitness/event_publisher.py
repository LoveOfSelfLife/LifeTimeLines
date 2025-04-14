from common.fitness.outbound_event_queue import OutboundEventQueue
import json

class EventPublisher:
    """
    EventPublisher is a class that used by the fitness app to publish events to the Azure storage queue.
    It is used to publish significant events that will be consumed by the fitness event processor.
    The event processor will interpret these events, which may include sending SMS messages to club members
    """
    def __init__(self):
        self.queue_client = OutboundEventQueue.get_queue_client()
        self.queue_name = OutboundEventQueue.queue_name

    def publish_event(self, event_type, event_data):
        """
        Publish an event to the Azure storage queue.
        :param event_type: The type of the event to publish.
        :param event_data: The data associated with the event.
        """
        event = {
            "event_type": event_type,
            "event_data": event_data
        }
        message = json.dumps(event)
        self.queue_client.send_message(message)  # Send the message to the queue
