from azure.core.exceptions import ResourceExistsError
from azure.storage.blob import BlobServiceClient, BlobClient

class BlobStore():
    connection_string = None

    @staticmethod
    def initialize(connection_string):
        BlobStore.connection_string = connection_string

    def __init__(self, container_name:str):
        if not self.connection_string:
            raise Exception("Table connection creds null")
        self.blob_service_client = BlobServiceClient.from_connection_string(conn_str=BlobStore.connection_string)
        self.container_name = container_name.lower()
        self.container_client = self.blob_service_client.get_container_client(container_name.lower())
        try:
            self.container_client.create_container()
            print("Created container")
        except ResourceExistsError:
            print("Container already exists")

    def upload_file(self, local_file_path, blob_name):
        with open(local_file_path, "rb") as data:
            self.upload(data, blob_name)
        print(f"File '{local_file_path}' uploaded to '{blob_name}' in container '{self.container_name}'")        
    
    def upload(self, data, blob_name):
        blob_client = self.container_client.get_blob_client(blob=blob_name)
        blob_client.upload_blob(data)

    def get_blob_client(self, blob_name):
        return self.container_client.get_blob_client(blob=blob_name)
    