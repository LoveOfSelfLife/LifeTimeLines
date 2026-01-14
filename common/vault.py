import os
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential, ClientSecretCredential

def get_creds_from_env():
    client_id = os.getenv('AZURE_CLIENT_ID', None)
    client_secret = os.getenv('AZURE_CLIENT_SECRET', None)
    tenant_id = os.getenv('TENANT_ID', None)
    if client_id and client_secret and tenant_id:
        return ClientSecretCredential(tenant_id, client_id, client_secret)
    else:
        return DefaultAzureCredential()

class Vault:

    def __init__(self, vault_name = "lifetimelines-secrets-1"):
        self.vault_name = vault_name
        self.key_vault_uri = f"https://{vault_name}.vault.azure.net"
        self.credential = get_creds_from_env()
        self.client = SecretClient(vault_url=self.key_vault_uri, credential=self.credential)
        
    def get_secret_from_vault(self, secret_name):
        try:
            val = self.client.get_secret(secret_name)
            return val.value
        except:
            return None

    def set_secret_to_vault(self, secret_name, secret_value):
        try:
            self.client.set_secret(secret_name, secret_value)
        except Exception as e:
            print(f'exception when attempting to set secret: {e}')





