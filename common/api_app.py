from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_restx import Api
from flask_cors import CORS   

import datetime
import signal
import sys
from types import FrameType

def create_api_app(namespaces=[], apiname='api', apiversion='1.0', apidescription=''):
    app : Flask = Flask(__name__, static_url_path='', static_folder='static')
    app.wsgi_app = ProxyFix(app.wsgi_app)
    app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RTxyz'
    
    api = Api(
        etitle=apiname,
        version=apiversion,
        description=apidescription
    )
    for ns in namespaces:
        api.add_namespace(ns)

    api.init_app(app)
    
    CORS(app)  

    signal.signal(signal.SIGTERM, shutdown_handler)
    return app

# https://cloud.google.com/blog/topics/developers-practitioners/graceful-shutdowns-cloud-run-deep-dive
# [START cloudrun_sigterm_handler]
def shutdown_handler(signal: int, frame: FrameType) -> None:
    # logger.info("Signal received, safely shutting down.")
    # database.shutdown()
    # middleware.logging_flush()
    print("Exiting process.", flush=True)
    # sys.exit(0)
