import os
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

class Vault:

    def __init__(self, vault_name):
        self.vault_name = vault_name
        self.KVUri = f"https://{vault_name}.vault.azure.net"
        self.credential = DefaultAzureCredential()
        self.client = SecretClient(vault_url=self.KVUri, credential=self.credential)
        
    def get_secret_from_vault(self, secret_name):
        val = self.client.get_secret(secret_name)
        return val

    def set_secret_to_vault(self, secret_name, secret_value):
        val = self.client.set_secret(secret_name, secret_value)
        return val




