import os
import sys
import signal

from flask import Flask, jsonify
from flask_cors import CORS   
from werkzeug.middleware.proxy_fix import ProxyFix

from dotenv import load_dotenv
from main import main
from backend_svcs import main as backend_main
from contacts_model import Contact

def create_app():
    load_dotenv()

    Contact.load_db()

    app : Flask = Flask(__name__)
    app.wsgi_app = ProxyFix(app.wsgi_app)
    app.secret_key = 'A0Zr98j/3yX R~XHH!jmN;aljsfsjd'

    app.register_blueprint(main)
    app.register_blueprint(backend_main)

    CORS(app)  

    signal.signal(signal.SIGTERM, shutdown_handler)
    return app

# https://cloud.google.com/blog/topics/developers-practitioners/graceful-shutdowns-cloud-run-deep-dive
# [START cloudrun_sigterm_handler]
def shutdown_handler(signal: int, frame) -> None:
    # logger.info("Signal received, safely shutting down.")
    # database.shutdown()
    # middleware.logging_flush()
    print("Exiting the LifeTimeLines process.", flush=True)
    # sys.exit(0)


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
