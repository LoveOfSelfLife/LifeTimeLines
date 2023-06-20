import os
from dotenv import load_dotenv
from common.api_app import create_api_app
from common.tables import TableStore
from person_entity_api_routes import pns as person_entity_ns
from location_entity_api_routes import lns as location_entity_ns

API_DEFINITION = {  "namespaces": [person_entity_ns, location_entity_ns], 
                    "apiname": "Entities API", 
                    "apiversion": '1.0', 
                    "apidescription": ''
    }

def create_app():
    load_dotenv()
    TableStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))
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

