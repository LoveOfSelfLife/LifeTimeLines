from flask import session
import os
import google.oauth2.credentials
import json
from flask_restx import Namespace, Resource
from flask import session, request, url_for, redirect
from google_auth_oauthlib.flow import Flow
import common.encoder
from common.vault import Vault

GOOGLE_SCOPES = ['https://www.googleapis.com/auth/photoslibrary.readonly', \
                 'https://www.googleapis.com/auth/gmail.readonly', \
                 'https://www.googleapis.com/auth/drive.readonly']


def get_config_from_secret():
    config_js = None
    if config_str := os.getenv('GOOGLE_CLIENT_SECRET_BASE64', None):
        config_str = common.encoder.decode(config_str)
        config_js = json.loads(config_str)
    return config_js

def get_credentials(scopes=GOOGLE_SCOPES):
    try:
        if 'credentials' in session and session['credentials'] is not None:
            print(f'using credentials found in session')
            session['credentials']['scopes'] = scopes
            if refresh_token := session['credentials']['refresh_token']:
                store_refresh_token(refresh_token)
            return google.oauth2.credentials.Credentials(**session['credentials'])
    except:
        pass

    if refresh_token := get_refresh_token():
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
            print('using refresh_token found stored in order to refresh credentials')
            return google.oauth2.credentials.Credentials(**credentials)

    print('credentials not found in session or in file system')
    return None

def get_refresh_token():
    kv = Vault()
    if refresh_token := kv.get_secret_from_vault("refreshtoken"):
        print("found refresh_token in keyvault")
        return refresh_token
    return None

def store_refresh_token(refresh_token):
    if not refresh_token:
        print('refresh token is None - cannot store refresh token')
    else:
        print('storing refresh token to keyvault')
        kv = Vault()
        kv.set_secret_to_vault("refreshtoken", str(refresh_token))

def google_doauth(url_auth_shorthand):
    print('in /doauth')

    if client_config := get_config_from_secret():
        flow = Flow.from_client_config(client_config=client_config, scopes=GOOGLE_SCOPES)
    else:
        return "NO SECRET"

    # The URI created here must exactly match one of the authorized redirect URIs
    # for the OAuth 2.0 client, which you configured in the API Console. If this
    # value doesn't match an authorized URI, you will get a 'redirect_uri_mismatch'
    # error.
    flow.redirect_uri = url_for(url_auth_shorthand, _scheme='https', _external=True)
    if 'localhost' in flow.redirect_uri or '127.0.0' in flow.redirect_uri:
        flow.redirect_uri = url_for(url_auth_shorthand, _scheme='http', _external=True)
    
    authorization_url, state = flow.authorization_url(
    # Enable offline access so that you can refresh an access token without
    # re-prompting the user for permission. Recommended for web server apps.
    access_type='offline',
    # Enable incremental authorization. Recommended as a best practice.
    include_granted_scopes='true')

    # Store the state so the callback can verify the auth server response.
    session['state'] = state
    print(f"redirecting to URL: {authorization_url}")
    redirect_url = redirect(authorization_url)
    return redirect_url


def google_auth(url_auth_shorthand, url_whendone_shorthand):
    print('in /auth')
    # Specify the state when creating the flow in the callback so that it can
    # verified in the authorization server response.
    state = session['state']

    if client_config := get_config_from_secret():
        flow = Flow.from_client_config(client_config=client_config, scopes=GOOGLE_SCOPES, state=state)
    else:
        return "NO SECRET"
    
    flow.redirect_uri = url_for(url_auth_shorthand, _scheme='https', _external=True)
    if 'localhost' in flow.redirect_uri or '127.0.0' in flow.redirect_uri:
        flow.redirect_uri = url_for(url_auth_shorthand, _scheme='http', _external=True)

    url = request.url
    if not ('localhost' in flow.redirect_uri or '127.0.0' in flow.redirect_uri):
    # if 'localhost' not in flow.redirect_uri:
        if request.url.startswith('http://'):
            url = request.url.replace('http://', 'https://', 1)

    authorization_response = url
    flow.fetch_token(authorization_response=authorization_response)

    # Store the credentials in the session & store refresh token in storage
    session['credentials'] = {
        'token': flow.credentials.token,
        'refresh_token': flow.credentials.refresh_token,
        'token_uri': flow.credentials.token_uri,
        'client_id': flow.credentials.client_id,
        'client_secret': flow.credentials.client_secret,
        'scopes': flow.credentials.scopes}    
    
    store_refresh_token(flow.credentials.refresh_token)

    return redirect(url_for(url_whendone_shorthand))


auth_ns = Namespace('auth', description='services to sync with google photos', path='/')

@auth_ns.route('/doauth')
class DoAuth(Resource):

    def get(self):
        return google_doauth()
    
@auth_ns.route('/auth')
class Auth(Resource):

    def get(self):
        return google_auth()
    
@auth_ns.route('/status')
class Status(Resource):
    def get(self):
        credentials = get_credentials(GOOGLE_SCOPES)
        if credentials:
            return "logged in"
        else:
            return "logged OUT"

