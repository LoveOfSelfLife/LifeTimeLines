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
        
        # Version and build information
        Env.BUILD_NUMBER = os.getenv("BUILD_NUMBER", "dev")
        Env.BUILD_DATE = os.getenv("BUILD_DATE", None)
        Env.BUILD_COMMIT = os.getenv("BUILD_COMMIT", "unknown")
        Env.BUILD_BRANCH = os.getenv("BUILD_BRANCH", "development")
        
        if Env.AZURE_CLIENT_SECRET:
            m = hashlib.sha256()
            m.update(Env.AZURE_CLIENT_SECRET.encode())
            Env.SECRET_KEY = m.hexdigest()

    @staticmethod
    def is_running_in_azure() -> bool:
        """
        Returns True if the application is running inside Azure Container Apps, 
        and False if it is running locally on your laptop.
        """
        # Azure Container Apps injects these platform metadata variables automatically
        return os.getenv("CONTAINER_APP_NAME") is not None
    