import os
from dotenv import load_dotenv
from common.api_app import create_api_app
from orch_api_routes import ns as orch_ns

API_DEFINITION = {  "namespaces": [orch_ns], 
                    "apiname": "Orchestration Manager API", 
                    "apiversion": '1.0', 
                    "apidescription": ''
    }

def create_app():
    load_dotenv()
    return create_api_app(**API_DEFINITION)

if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=8080, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port
    
    # make sure to not set this in production
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    
    app = create_app()
    app.run(port=port)

