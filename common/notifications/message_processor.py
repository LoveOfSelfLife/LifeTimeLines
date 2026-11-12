import logging

from common.http_requests import send_internal_request

def process_fitness_message(msg_data, auth_token=None):
    logger = logging.getLogger(__name__)
    if auth_token:
        length = len(auth_token)
        logger.info(f'Auth token length: {length}')
        # only show the first 10 characters of the auth token for security reasons
        logger.info(f'Auth token provided: {auth_token[:10]}')
        # get the current time, then check if the current time is within 5 minutes of the top of the hour
        import datetime
        now = datetime.datetime.utcnow()
        window = 2
        if now.minute <= window or now.minute >= 60 - window:
            logger.info(f'Current time is within {window} minutes of the top of the hour')
            response = send_internal_request('fitnessclub', auth_token=auth_token)
            if response is None:
                logger.error('Internal request returned no data')
            else:
                logger.info(f'Internal request response: {response}')
    else:
        logger.info('No auth token provided')
    logger.info(f'Processing fitness message: {msg_data}')
    pass
