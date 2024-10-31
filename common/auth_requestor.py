import msal
import os

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

class ApiTokenRequestor():
    def __init__(self):
        AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
        AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
        TENANT_ID = os.getenv("TENANT_ID")

        self.scope = [f"api://{AZURE_CLIENT_ID}/.default"]
        self.auth_requestor = AuthRequestor(TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, self.scope)
        
        self.app = msal.ConfidentialClientApplication(
            client_id=AZURE_CLIENT_ID, 
            authority=f"https://login.microsoftonline.com/{TENANT_ID}",
            client_credential=AZURE_CLIENT_SECRET
            )

    def get_token(self):
        return self.auth_requestor.get_auth_token()
