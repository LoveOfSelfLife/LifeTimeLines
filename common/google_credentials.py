from flask import session
import os
import google.oauth2.credentials
import json
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
