from flask_restx import Namespace, Resource, reqparse, fields
from flask import make_response, request, url_for, redirect
import datetime
import json
from common.auth_requestor import AuthRequestor
from common.jwt_auth import requires_auth
from common.google_credentials import google_doauth, google_auth
from flask import render_template
import os
from common.vault import Vault

ns = Namespace('echos', description='echo api')

class Cache():
    cache_body = None
    def __init__(self):
        pass

@ns.route('/token')
class Health(Resource):
    ''' '''
    @ns.doc('token')
    @requires_auth    
    def get(self):
        AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
        AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
        TENANT_ID = os.getenv("TENANT_ID")

        scope = [f"api://{AZURE_CLIENT_ID}/.default"]
        auth = AuthRequestor(TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, scope)
        token = auth.get_auth_token()
        return {"token": token}
    

@ns.route('/set-key/<key>/<val>')
class GoogleDoAuth(Resource):
    ''' '''
    @ns.doc('set-key')
    def get(self, key, val):
        kv = Vault()
        kv.set_secret_to_vault(key, val)
        return f"key: <{key}> set to value: <{val}>"

@ns.route('/get-key/<key>')
class GoogleDoAuth(Resource):
    ''' '''
    @ns.doc('get-key')
    def get(self, key):
        kv = Vault()
        if val := kv.get_secret_from_vault(key):
            return val
        else:
            return "not found", 404
        
@ns.route('/refresh')
class GoogleDoAuth(Resource):
    ''' '''
    @ns.doc('refresh')
    def get(self):
        return make_response(render_template('refresh.html'))

@ns.route('/doauth')
class GoogleDoAuth(Resource):
    ''' '''
    @ns.doc('doauth')
    def get(self):
        return google_doauth('echos_google_auth')

@ns.route('/auth')
class GoogleAuth(Resource):
    ''' '''
    @ns.doc('auth')
    def get(self):
        return google_auth('echos_google_auth', 'echos_google_done')

@ns.route('/done')
class GoogleDone(Resource):
    ''' '''
    @ns.doc('auth')
    def get(self):
        return make_response(render_template('done.html'))

@ns.route('/echo')
class Echo(Resource):
    ''' '''
    @ns.doc('echo')
    def get(self):
        req = []
        print(request.url)
        req.append({"URL": request.url})
        for n,v in request.headers:
            req.append({ n : v })
        return req
    
    @ns.doc('create data to be echoed')
    def post(self):
        req = []
        print(request.url)
        req.append({"URL": request.url})
        for n,v in request.headers:
            req.append({ n : v })
        body = request.get_json(silent=True)
        if body:
            req.append({"BODY": body})
        else:
            req.append({"BODY": "no body"})

        Cache.cache_body = req
            
        return req, 201

@ns.route('/abc')
class EchoAbc(Resource):
    ''' '''
    @ns.doc('echo')
    @requires_auth
    def get(self):
        req = []
        if Cache.cache_body:
            req.append({ "PREV_POST" : Cache.cache_body})
        return req
    
    @ns.doc('create data to be echoed')
    def post(self):
        req = []
        print(request.url)
        req.append({"URL": request.url})
        for n,v in request.headers:
            req.append({ n : v })
        body = request.get_json(silent=True)
        if body:
            req.append({"BODY": body})
        else:
            req.append({"BODY": "no body"})

        Cache.cache_body = req
            
        return req, 201


