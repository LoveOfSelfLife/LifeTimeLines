
from azure.data.tables import TableClient

class EntityTable():
    connection_string = None

    @staticmethod
    def initialize(connection_string):
        EntityTable.connection_string = connection_string

    def __init__(self, table_name:str):
        if not self.connection_string:
            raise Exception("Table connection creds null")
        
        self.table_client = TableClient.from_connection_string(conn_str=EntityTable.connection_string, table_name=table_name)

