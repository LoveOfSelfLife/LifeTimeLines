import os
from dotenv import load_dotenv
from common.api_app import create_api_app
from common.discovery import get_service_port
from .google_auth_api_routes import ns as auth_ns
from photos_api_routes import ns as photos_ns
from photos_task_routes import ns as tasks_ns

API_DEFINITION = {  "namespaces": [tasks_ns, photos_ns, auth_ns], 
                    "apiname": "Photos Operations API", 
                    "apiversion": '1.0', 
                    "apidescription": ''
    }

def create_app():
    load_dotenv()
    return create_api_app(**API_DEFINITION)

if __name__ == '__main__':
    from argparse import ArgumentParser

    port = get_service_port('photos')
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=port, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port
    
    # make sure to not set this in production
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    
    app = create_app()
    app.run(port=port)

