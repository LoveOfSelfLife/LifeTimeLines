from flask import Flask
from flask_restx import Api
from flask_cors import CORS   
from werkzeug.middleware.proxy_fix import ProxyFix

import sys
import signal
import logging
from types import FrameType

from common.jwt_auth import AuthHandler, AuthError
from common.env_context import Env
from common.env_init import initialize_environment

def create_api_app(namespaces=[], apiname='api', apiversion='1.0', apidescription=''):
    app : Flask = Flask(__name__, static_url_path='', static_folder='static', template_folder='../templates')
    app.wsgi_app = ProxyFix(app.wsgi_app)
    app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RTxyz'

    # Configure logging
    app.logger.setLevel(logging.INFO)
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)  # Adjust level as needed (e.g., DEBUG, INFO, WARNING)
    logger = logging.getLogger(__name__)

    initialize_environment()

    AuthHandler(Env.TENANT_ID, Env.AZURE_CLIENT_ID)
    
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

    # Usage example
    logger.info("This is an info log message. in the create_api_app function in api_app.py")

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
