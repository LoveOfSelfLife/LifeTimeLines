import os
from dotenv import load_dotenv
import hashlib

class Env :
    def initialize():

        Env.AZURE_STORAGETABLE_CONNECTIONSTRING = os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None)
        Env.AZURE_FILESHARE_CONNECTIONSTRING = os.getenv('AZURE_FILESHARE_CONNECTIONSTRING', None)
        Env.TENANT_ID = os.getenv('TENANT_ID', None)
        Env.AZURE_CLIENT_ID = os.getenv('AZURE_CLIENT_ID', None)
        Env.AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET", None)
        Env.ORCH_TESTING_MODE = os.getenv("ORCH_TESTING_MODE", None)
        Env.GOOGLE_CLIENT_SECRET_BASE64 = os.getenv("GOOGLE_CLIENT_SECRET_BASE64", None)
        Env.SESSION_DIR = os.getenv("SESSION_DIR", None)
        
        if Env.AZURE_CLIENT_SECRET:
            m = hashlib.sha256()
            m.update(Env.AZURE_CLIENT_SECRET.encode())
            Env.SECRET_KEY = m.hexdigest()
