import logging

from common.http_requests import send_internal_request

def process_fitness_message(msg_data, auth_token=None):
    logger = logging.getLogger(__name__)
    if auth_token:
        length = len(auth_token)
        logger.info(f'Auth token length: {length}')
        # only show the first 10 characters of the auth token for security reasons
        logger.info(f'Auth token provided: {auth_token[:10]}')
        send_internal_request('fitnessclub', auth_token=auth_token)
    else:
        logger.info('No auth token provided')
    logger.info(f'Processing fitness message: {msg_data}')
    pass
