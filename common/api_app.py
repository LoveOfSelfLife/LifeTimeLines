import os
from flask import Flask, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_restx import Api
from flask_cors import CORS   

import datetime
import signal
import sys
from types import FrameType

from common.table_store import TableStore
from common.queue_store import QueueStore
from common.jwt_auth import AuthHandler, AuthError

def create_api_app(namespaces=[], apiname='api', apiversion='1.0', apidescription=''):
    app : Flask = Flask(__name__, static_url_path='', static_folder='static', template_folder='../templates')
    app.wsgi_app = ProxyFix(app.wsgi_app)
    app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RTxyz'
        
    TableStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))
    QueueStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))
    
    AuthHandler(os.getenv('TENANT_ID', None), os.getenv('AZURE_CLIENT_ID', None))
    
    api = Api(
        title=apiname,
        version=apiversion,
        description=apidescription
    )
    for ns in namespaces:
        api.add_namespace(ns)

    @api.errorhandler(AuthError)
    def handle_auth_error(ex):
        return { 'message': ex.error['code'], 'description' : ex.error['description'] },ex.status_code

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
    print("Exiting the LifeTimeLines process.", flush=True)
    # sys.exit(0)
