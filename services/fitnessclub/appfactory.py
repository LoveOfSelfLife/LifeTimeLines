import os
import signal

from flask import Flask
from flask_cors import CORS   
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv
from common.discovery import get_service_port
from base import bp as base_bp
from views.schedule.routes import bp as schedule_bp
from views.program.routes import bp as program_bp
from views.configurations.routes import bp as configurations_bp
from common.env_init import initialize_environment
from common.env_context import Env
from auth import auth
import app_config

def create_app():
    load_dotenv()
    initialize_environment()
    
    app : Flask = Flask(__name__)
    app.config['EXPLAIN_TEMPLATE_LOADING'] = True
    app.wsgi_app = ProxyFix(app.wsgi_app)
    app.secret_key = Env.SECRET_KEY
    app.config.from_object(app_config)
    auth.init_app(app)

    for bp in [base_bp, 
               configurations_bp, 
               schedule_bp, 
               program_bp]:
        app.register_blueprint(bp, url_prefix=f'/{bp.name}')

    CORS(app)  

    signal.signal(signal.SIGTERM, shutdown_handler)
    return app

def shutdown_handler(signal: int, frame) -> None:
    print("Exiting the FitnessClub process.", flush=True)

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()

    port = 8087

    parser.add_argument('-p', '--port', default=port, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port
    
    # make sure to not set this in production
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    
    app = create_app()
    
    app.run(port=port, use_reloader=False)
