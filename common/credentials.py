from flask_restx import Namespace, fields
from flask import session
import os
import google.oauth2.credentials
import json

def get_credentials(scopes):
    if 'credentials' in session and session['credentials'] is not None:
        print('using credentials found in session')
        session['credentials']['scopes'] = scopes
        return google.oauth2.credentials.Credentials(**session['credentials'])

    elif refresh_token := get_refresh_token():
        if client_config_str := os.getenv('GOOGLE_CLIENT_SECRET', None):
            client_config = json.loads(client_config_str)
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

