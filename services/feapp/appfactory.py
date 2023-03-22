import os
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_restx import Api
from feapp import ns as feapp_ns
from flask_cors import CORS

def create_app(test_config=None):
    app = Flask(__name__, static_url_path='', static_folder='static')
    app.wsgi_app = ProxyFix(app.wsgi_app)

    try:
        app.config["TEST_ENV_VARIABLE"] = os.environ['TEST_ENV_VARIABLE']
    except KeyError:
        print('variable not set')

    fe_api = Api(
        etitle='FE APIs',
        version='1.0',
        description='THese are some APIs for the front-end app',
    )
    fe_api.add_namespace(feapp_ns)
    fe_api.init_app(app)
    
    CORS(
        app,
        resources={r"/*": {"origins": 'http://localhost:3000'}},
        allow_headers=["Authorization", "Content-Type"],
        methods=["GET"],
        max_age=86400,
        supports_credentials=True
    )
    return app

if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    app = create_app()
    app.run(port=port)

