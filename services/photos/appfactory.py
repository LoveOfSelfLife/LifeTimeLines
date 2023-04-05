import os
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_restx import Api
from sync import ns as sync_ns
# from common.credentials import auth_ns as auth_ns
import common.credentials
from dotenv import load_dotenv
from flask_cors import CORS

def create_app(test_config=None):
    load_dotenv()
    app : Flask = Flask(__name__, static_url_path='', static_folder='static')
    app.wsgi_app = ProxyFix(app.wsgi_app)
    # need to set the secret_key otherwise will receive Internal Server Error when attemping to save state
    # as per: https://stackoverflow.com/questions/18139910/internal-server-error-when-using-flask-session
    app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RTxyz'
    
    sync_api = Api(
        etitle='Photos API',
        version='1.0',
        description='sync with google photos'
    )
    sync_api.add_namespace(sync_ns)
    sync_api.add_namespace(common.credentials.auth_ns)
    sync_api.init_app(app)

    CORS(app)  
    return app

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

