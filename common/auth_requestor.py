import msal

class AuthRequestor() :
    def __init__(self, tenant, client_id, client_secret, scope):
        # Create a preferably long-lived app instance which maintains a token cache.
        self.app = msal.ConfidentialClientApplication(
            client_id=client_id, 
            authority=f"https://login.microsoftonline.com/{tenant}",
            client_credential=client_secret
            )
        self.scope = scope

    def get_auth_token(self):
        result = self.app.acquire_token_silent(self.scope, account=None)
        if not result:
            result = self.app.acquire_token_for_client(scopes=self.scope)

        if "access_token" in result:
            token = result['access_token']
            return token
        else:
            print(result.get("error"))
            print(result.get("error_description"))
            print(result.get("correlation_id"))  # You may need this when reporting a bug
            raise Exception(f'cannot get auth token') 
