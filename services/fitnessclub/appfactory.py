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
from views.home.home_routes import bp as home_bp
from views.schedule.schedule_routes import bp as schedule_bp
from views.program.programs_routes import bp as program_bp
from views.exercises.exercise_routes import bp as exercises_bp
from views.profile.profile_routes import bp as profile_bp
from views.admin.admin_routes import bp as admin_bp
from views.members.exercises_routes import bp as members_bp
from views.workouts.workout_routes import bp as workouts_bp
from common.env_init import initialize_environment
from common.env_context import Env
from auth import auth
from datetime import timedelta
from version import get_version_info
import redis

from flask import session
from flask_session import Session

def create_app():
    load_dotenv()
    initialize_environment()
    
    app : Flask = Flask(__name__)
    # app.config['EXPLAIN_TEMPLATE_LOADING'] = True
    app.wsgi_app = ProxyFix(app.wsgi_app)
    app.secret_key = Env.SECRET_KEY

    # Configure Redis and Flask-Session
    app.config['SESSION_TYPE'] = 'redis'
    app.config['SESSION_PERMANENT'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=365)  # Set session lifetime to 1 year
    app.config['SESSION_USE_SIGNER'] = True
    app.config['SESSION_REDIS'] = redis.from_url('redis://rediscache:6379' if not Env.ORCH_TESTING_MODE else 'redis://localhost:6379')

    # Initialize session extension
    Session(app)

    auth.init_app(app)

    # Make version information available to all templates
    @app.context_processor
    def inject_version_info():
        return {'version_info': get_version_info()}

    for bp in [base_bp, 
               home_bp,
               admin_bp, 
               schedule_bp, 
               program_bp,
               profile_bp,
               exercises_bp,
               members_bp,
               workouts_bp]:
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
