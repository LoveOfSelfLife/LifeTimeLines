from flask_restx import Namespace, Resource, reqparse, fields
from flask import request, url_for, redirect
import datetime
import json
from common.jwt_auth import requires_auth

ns = Namespace('echos', description='echo api')

class Cache():
    cache_body = None
    def __init__(self):
        pass

@ns.route('/')
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


