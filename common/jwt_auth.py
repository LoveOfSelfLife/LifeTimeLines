from flask import Flask, request, jsonify, _request_ctx_stack
from cryptography.hazmat.primitives import serialization
import requests
import json
import jwt
from functools import wraps

class AuthHandler():
    public_key = None
    _jwks_url = None
    app_id = None

    def __init__(self, tenant, app_id):
        AuthHandler._jwks_url = f"https://login.microsoftonline.com/{tenant}/discovery/v2.0/keys"
        AuthHandler.app_id = app_id

    @staticmethod
    def get_public_key_for_token(token_kid):
        if AuthHandler.public_key:
            return AuthHandler.public_key
            
        response = requests.get(AuthHandler._jwks_url, verify=False)
        keys = response.json()['keys']
        public_key = None    
        for key in keys:
            if key['kid'] == token_kid:
                public_key = key

        rsa_pem_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(public_key))
        AuthHandler.public_key = rsa_pem_key.public_bytes(
            encoding=serialization.Encoding.PEM, 
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        return AuthHandler.public_key

    @staticmethod
    def get_token_auth_header():
        """Obtains the Access Token from the Authorization Header
        """
        auth = request.headers.get("Authorization", None)
        if not auth:
            raise AuthError({"code": "authorization_header_missing",
                            "description":
                                "Authorization header is expected"}, 401)

        parts = auth.split()

        if parts[0].lower() != "bearer":
            raise AuthError({"code": "invalid_header",
                            "description":
                                "Authorization header must start with"
                                " Bearer"}, 401)
        elif len(parts) == 1:
            raise AuthError({"code": "invalid_header",
                            "description": "Token not found"}, 401)
        elif len(parts) > 2:
            raise AuthError({"code": "invalid_header",
                            "description":
                                "Authorization header must be"
                                " Bearer token"}, 401)

        token = parts[1]
        return token

# Error handler
class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code

def requires_auth(f):
    """Determines if the Access Token is valid
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = AuthHandler.get_token_auth_header()

        unverified_token_claims = jwt.decode(token, options={"verify_signature": False})
        unverified_token_headers = jwt.get_unverified_header(token)
        token_alg = unverified_token_headers['alg']
        token_kid = unverified_token_headers['kid']

        rsa_pem_key_bytes = AuthHandler.get_public_key_for_token(token_kid)
        
        if rsa_pem_key_bytes:
            try:
                payload = jwt.decode(
                    token,
                    key=rsa_pem_key_bytes,
                    algorithms=token_alg,
                    audience=AuthHandler.app_id,
                    verify=True,
                    options={"verify_signature": True}
                )
            except jwt.ExpiredSignatureError:
                raise AuthError({"code": "token_expired",
                                "description": "token is expired"}, 401)
            except jwt.JWTClaimsError:
                raise AuthError({"code": "invalid_claims",
                                "description":
                                    "incorrect claims,"
                                    "please check the audience and issuer"}, 401)
            except jwt.InvalidSignatureError:
                # The JWT token is invalid
                print('The JWT token is invalid.')
                raise AuthError({"code": "invalid signature",
                                "description": "token signature is not valid"}, 401)                
            except jwt.DecodeError:
                # The JWT token could not be decoded
                print('The JWT token could not be decoded.')             
                raise AuthError({"code": "cannot decode",
                                "description": "token could not be decoded"}, 401)                
            except Exception:
                raise AuthError({"code": "invalid_header",
                                "description":
                                    "Unable to parse authentication"
                                    " token."}, 401)

            _request_ctx_stack.top.current_user = payload
            return f(*args, **kwargs)
        raise AuthError({"code": "invalid_header",
                        "description": "Unable to find appropriate key"}, 401)
    return decorated


if __name__ == '__main__':
    pass
