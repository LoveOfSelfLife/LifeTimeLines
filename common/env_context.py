import os

class Env :
    # AZURE_STORAGETABLE_CONNECTIONSTRING = os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None)
    # AZURE_FILESHARE_CONNECTIONSTRING = AZURE_STORAGETABLE_CONNECTIONSTRING
    # TENANT_ID = os.getenv('TENANT_ID', None)
    # AZURE_CLIENT_ID = os.getenv('AZURE_CLIENT_ID', None)

    def initialize():
        Env.AZURE_STORAGETABLE_CONNECTIONSTRING = os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None)
        Env.AZURE_FILESHARE_CONNECTIONSTRING = os.getenv('AZURE_FILESHARE_CONNECTIONSTRING', None)
        Env.TENANT_ID = os.getenv('TENANT_ID', None)
        Env.AZURE_CLIENT_ID = os.getenv('AZURE_CLIENT_ID', None)
