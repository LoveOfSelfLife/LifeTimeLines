import os
import signal

from flask import Flask
from flask_cors import CORS   
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv

from base import bp as base_bp
from views.view1.routes import bp as view1_bp
from views.view2.routes import bp as view2_bp
from views.contacts.routes import bp as contacts_bp
from views.orchestration.routes import bp as orchestration_bp
from views.tables.routes import bp as tables_bp
from views.services.routes import bp as services_bp
from views.processes.routes import bp as processes_bp

from views.contacts.routes import init as contacts_init
from views.contacts.contacts_model import Contact
from common.env_init import initialize_environment

def create_app():

    load_dotenv()
    initialize_environment()
    contacts_init()

    app : Flask = Flask(__name__)
    app.wsgi_app = ProxyFix(app.wsgi_app)
    app.secret_key = 'A0Zr98j/3yX R~XHH!jmN;aljsfsjd'

    app.register_blueprint(base_bp)
    app.register_blueprint(contacts_bp, url_prefix='/contacts')
    app.register_blueprint(orchestration_bp, url_prefix='/orchestration')
    app.register_blueprint(view1_bp, url_prefix='/view1')
    app.register_blueprint(view2_bp, url_prefix='/view2')
    app.register_blueprint(tables_bp, url_prefix='/tables')
    app.register_blueprint(services_bp, url_prefix='/services')
    app.register_blueprint(processes_bp, url_prefix='/processes')

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
