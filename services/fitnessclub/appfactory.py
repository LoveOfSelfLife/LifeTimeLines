import os
import signal

from cachelib import FileSystemCache
from flask import Flask
from flask_cors import CORS   
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv
from common.discovery import get_service_port
from base import bp as base_bp
from views.schedule.routes import bp as schedule_bp
from views.program.routes import bp as program_bp
from views.profile.routes import bp as profile_bp
from views.configurations.routes import bp as configurations_bp
from common.env_init import initialize_environment
from common.env_context import Env
from auth import auth
from datetime import timedelta

class AzureFileSystemCache(FileSystemCache):
    def _run_safely(self, fn, *args, **kwargs):
        if fn.__name__ == 'chmod':
            return None
        else:
            return super()._run_safely(fn, *args, **kwargs)
    def _get_filename(self, key: str) -> str:
        filename = super()._get_filename(key)
        print(f"session key: {key}, filename: {filename}")
        return filename
    
# # Use this in your Flask configuration
# app.config['SESSION_CLIENT'] = AzureFileSystemCache(
#     cache_dir='/share/FitnessClub/sessions',  # Your Azure file share path
#     threshold=1000,
#     mode=0o600  # This won't be applied due to the override
# )

def create_app():
    load_dotenv()
    initialize_environment()
    
    app : Flask = Flask(__name__)
    app.config['EXPLAIN_TEMPLATE_LOADING'] = True
    app.wsgi_app = ProxyFix(app.wsgi_app)
    app.secret_key = Env.SECRET_KEY
    # Set the session type to 'filesystem'
    app.config['SESSION_TYPE'] = 'filesystem'    

    

    if Env.SESSION_DIR:
        SESSION_DIR = Env.SESSION_DIR
    else:
        SESSION_DIR = '/share/FitnessClub/sessions'

    # Create a FileSystemCache instance:
    # - directory: path to store the session files (ensure the directory exists or create it)
    # - threshold: maximum number of cached items (optional, default might be 500)
    # - mode: file permissions (for example, 0o600 means read/write for the owner only)
    app.config['SESSION_CLIENT'] = AzureFileSystemCache(
        cache_dir=SESSION_DIR,  # Change to your desired directory path
        threshold=1000,       # Set as needed (default is often 500)
        mode=0o666            # Set file permissions; this is similar to the old SESSION_FILE_MODE
    )
    app.config['SESSION_FILE_DIR'] = SESSION_DIR
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=90)

    auth.init_app(app)

    for bp in [base_bp, 
               configurations_bp, 
               schedule_bp, 
               program_bp,
               profile_bp]:
        app.register_blueprint(bp, url_prefix=f'/{bp.name}')

    CORS(app)  

    app.session_interface.cache = app.config['SESSION_CLIENT']

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
