import os
import sys
import signal

from flask import Flask, jsonify
from flask_cors import CORS   
from werkzeug.middleware.proxy_fix import ProxyFix

from dotenv import load_dotenv
from common.api_app import shutdown_handler
from main import main
from contacts_model import Contact

def create_app():
    load_dotenv()

    Contact.load_db()

    app : Flask = Flask(__name__, static_url_path='')
    app.wsgi_app = ProxyFix(app.wsgi_app)
    app.secret_key = 'A0Zr98j/3yX R~XHH!jmN;aljsfsjd'

    app.register_blueprint(main)

    CORS(app)  

    signal.signal(signal.SIGTERM, shutdown_handler)
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
