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
from views.services.routes import bp as services_bp
from views.processes.routes import bp as processes_bp
from views.configurations.routes import bp as configurations_bp
from views.contacts.routes import init as contacts_init
from views.contacts.contacts_model import Contact
from common.env_init import initialize_environment
from common.env_context import Env

def create_app():
    load_dotenv()
    initialize_environment()
    contacts_init()
    
    app : Flask = Flask(__name__)
    app.config['EXPLAIN_TEMPLATE_LOADING'] = True
    app.wsgi_app = ProxyFix(app.wsgi_app)
    app.secret_key = Env.SECRET_KEY
    
    # app.register_blueprint(base_bp, url_prefix=f'/{base_bp.name}')
    
    for bp in [base_bp, 
               view1_bp, 
               view2_bp, 
               contacts_bp, 
               orchestration_bp, 
               configurations_bp, 
               services_bp, 
               processes_bp]:
        app.register_blueprint(bp, url_prefix=f'/{bp.name}')

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
