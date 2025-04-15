import json
import os
import sys
import logging

from datetime import datetime
from common.fitness.outbound_event_queue import OutboundEventQueue

def main() -> None:

    if connection_string := os.getenv("AZURE_STORAGETABLE_CONNECTIONSTRING") is None:
        raise Exception(f'You attempted to run the container without providing the AZURE_STORAGE_CONNECTION_STRING')

    logging.basicConfig(level=logging.INFO, stream=sys.stdout)  # Adjust level as needed (e.g., DEBUG, INFO, WARNING)
    logger = logging.getLogger(__name__)
    
    outbound_event_queue_client = OutboundEventQueue.get_queue_client(connection_string)
    logger.info(f'Client created for: {OutboundEventQueue.queue_name}')

    outbound_event_queue_client.send_message(json.dumps({"event": "periodic-time-event", "timestamp": datetime.now().isoformat()}))
    
    logger.info(f'Enqueued periodic time event message')
    logger.info(f'exiting container gracefully')
    exit(0)

if __name__ == '__main__':
    main()
