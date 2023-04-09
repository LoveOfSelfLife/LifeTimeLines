from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_restx import Api
from flask_cors import CORS   

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
    return app

