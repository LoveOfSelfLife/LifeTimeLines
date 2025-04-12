import os
import signal

# from cachelib import FileSystemCache
from cachelib import RedisCache
from flask import Flask
from flask_cors import CORS   
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv
from common.discovery import get_service_port
from base import bp as base_bp
from views.schedule.routes import bp as schedule_bp
from views.program.routes import bp as program_bp
from views.exercises.routes import bp as exercises_bp
from views.profile.routes import bp as profile_bp
from views.admin.routes import bp as admin_bp
from views.members.routes import bp as members_bp
from common.env_init import initialize_environment
from common.env_context import Env
from auth import auth
from datetime import timedelta

def create_app():
    load_dotenv()
    initialize_environment()
    
    app : Flask = Flask(__name__)
    app.config['EXPLAIN_TEMPLATE_LOADING'] = True
    app.wsgi_app = ProxyFix(app.wsgi_app)
    app.secret_key = Env.SECRET_KEY

    app.config['SESSION_TYPE'] = 'cachelib'
    app.config['SESSION_CACHELIB'] = RedisCache(
        host='rediscache' if not Env.ORCH_TESTING_MODE else 'localhost', 
        port=6379, 
        key_prefix='fitnessclub', 
        default_timeout=0
    )
    app.config['SESSION_PERMANENT'] = True # Optional, but recommended for persistent sessions
    app.config['SECRET_KEY'] = Env.SECRET_KEY
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=90)

    auth.init_app(app)

    for bp in [base_bp, 
               admin_bp, 
               schedule_bp, 
               program_bp,
               profile_bp,
               exercises_bp,
               members_bp
               ]:
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
