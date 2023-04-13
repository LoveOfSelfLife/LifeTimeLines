import os
from routes import photos_ns as photos_ns
from common.credentials import auth_ns
from common.api_app import create_api_app
from dotenv import load_dotenv
from common.tables import EntityTable

def create_app():
    load_dotenv()
    EntityTable.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))
                           
    return create_api_app([photos_ns, auth_ns], "Photos API", "1.0")

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

