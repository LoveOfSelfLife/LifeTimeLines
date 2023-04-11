from flask import session
import os
import google.oauth2.credentials
import json
from flask_restx import Namespace, Resource
from flask import session, request, url_for, redirect
from google_auth_oauthlib.flow import Flow
import common.encoder

GOOGLE_SCOPES = ['https://www.googleapis.com/auth/photoslibrary.readonly','https://www.googleapis.com/auth/gmail.readonly','https://www.googleapis.com/auth/drive.readonly']


def get_config_from_secret():
    config_js = None
    if config_str := os.getenv('GOOGLE_CLIENT_SECRET_BASE64', None):
        config_str = common.encoder.decode(config_str)
        config_js = json.loads(config_str)
    return config_js

def get_credentials(scopes):
    if 'credentials' in session and session['credentials'] is not None:
        print('using credentials found in session')
        session['credentials']['scopes'] = scopes
        return google.oauth2.credentials.Credentials(**session['credentials'])

    elif refresh_token := get_refresh_token():
        if client_config := get_config_from_secret():
            cfg = client_config['web']
            credentials = {
                'token': None,
                'refresh_token': refresh_token,
                'token_uri': cfg['token_uri'],
                'client_id': cfg['client_id'],
                'client_secret': cfg['client_secret'],
                'scopes': scopes
            }
            print('using refresh_token found in file system in order to refresh credentials')
            return google.oauth2.credentials.Credentials(**credentials)

    print('credentials not found in session or in file system')
    return None

def get_refresh_token():
    if refresh_token_store := os.getenv('REFRESH_TOKEN_STORE', None):
        try:
            with open(refresh_token_store, 'r') as rtf:
                refresh_token = rtf.readline()
                return refresh_token
        except OSError:
            return None
    return None

def store_credentials(credentials):
    session['credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes}
    if refresh_token_store := os.getenv('REFRESH_TOKEN_STORE', None):
        print('storing refresh token to file system')
        with open(refresh_token_store, 'w') as rtf:
            rtf.write(credentials.refresh_token)


auth_ns = Namespace('auth', description='services to sync with google photos', path='/')

@auth_ns.route('/doauth')
class DoAuth(Resource):

    def get(self):
        print('in /doauth')

        if client_config := get_config_from_secret():
            flow = Flow.from_client_config(client_config=client_config, scopes=GOOGLE_SCOPES)
        else:
            return "NO SECRET"

        # The URI created here must exactly match one of the authorized redirect URIs
        # for the OAuth 2.0 client, which you configured in the API Console. If this
        # value doesn't match an authorized URI, you will get a 'redirect_uri_mismatch'
        # error.
        flow.redirect_uri = url_for('auth_auth', _scheme='https', _external=True)
        if 'localhost' in flow.redirect_uri:
            flow.redirect_uri = url_for('auth_auth', _scheme='http', _external=True)
        
        authorization_url, state = flow.authorization_url(
        # Enable offline access so that you can refresh an access token without
        # re-prompting the user for permission. Recommended for web server apps.
        access_type='offline',
        # Enable incremental authorization. Recommended as a best practice.
        include_granted_scopes='true')

        # Store the state so the callback can verify the auth server response.
        session['state'] = state

        return redirect(authorization_url)

@auth_ns.route('/auth')
class Auth(Resource):

    def get(self):
        print('in /auth')
        # Specify the state when creating the flow in the callback so that it can
        # verified in the authorization server response.
        state = session['state']

        if client_config := get_config_from_secret():
            flow = Flow.from_client_config(client_config=client_config, scopes=GOOGLE_SCOPES, state=state)
        else:
            return "NO SECRET"
        
        flow.redirect_uri = url_for('auth_auth', _scheme='https', _external=True)
        if 'localhost' in flow.redirect_uri:
            flow.redirect_uri = url_for('auth_auth', _scheme='http', _external=True)

        url = request.url
        if 'localhost' not in flow.redirect_uri:
            if request.url.startswith('http://'):
                url = request.url.replace('http://', 'https://', 1)

        authorization_response = url
        flow.fetch_token(authorization_response=authorization_response)

        # Store the credentials in the session & store refresh token in storage
        store_credentials(flow.credentials)

        return redirect(url_for('photos_sync_operations_list'))

@auth_ns.route('/status')
class Status(Resource):
    def get(self):
        credentials = get_credentials(GOOGLE_SCOPES)
        if credentials:
            return "logged in"
        else:
            return "logged OUT"

