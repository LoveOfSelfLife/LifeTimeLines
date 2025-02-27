import os
from dotenv import load_dotenv
from common.api_app import create_api_app
from common.discovery import get_service_port
from person_entity_api_routes import ns as person_entity_ns
from location_entity_api_routes import ns as location_entity_ns
from generic_entity_api_routes import ns as genericn_entity_ns
import logging

API_DEFINITION = {  "namespaces": [person_entity_ns, location_entity_ns, genericn_entity_ns], 
                    "apiname": "Entities API", 
                    "apiversion": '1.0', 
                    "apidescription": ''
    }
logger = logging.getLogger(__name__)

def create_app():
    load_dotenv()
    return create_api_app(**API_DEFINITION)

if __name__ == '__main__':
    from argparse import ArgumentParser

    port = get_service_port('entities')
    print(f"got service port: {port}")
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=port, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port
    logger.info(f"Starting server on port {port}")

    # make sure to not set this in production
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    
    app = create_app()
    
    app.run(port=port)

