from flask_restx import Namespace, Resource, reqparse, fields
from flask import make_response, request, url_for, redirect
import datetime
import json
from common.jwt_auth import requires_auth
from common.google_credentials import google_doauth, google_auth
from flask import render_template
import os

ns = Namespace('echos', description='echo api')

class Cache():
    cache_body = None
    def __init__(self):
        pass


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
        return google_doauth()

@ns.route('/auth')
class GoogleAuth(Resource):
    ''' '''
    @ns.doc('auth')
    def get(self):
        return google_auth()

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


