

from azure.data.tables import TableClient, TableTransactionError
from azure.core.exceptions import ResourceExistsError

class EntityTable():
    connection_string = None

    @staticmethod
    def initialize(connection_string):
        EntityTable.connection_string = connection_string

    def __init__(self, table_name:str):
        if not self.connection_string:
            raise Exception("Table connection creds null")
        self.table_client = TableClient.from_connection_string(conn_str=EntityTable.connection_string, table_name=table_name)
        try:
            self.table_client.create_table()
            print("Created table")
        except ResourceExistsError:
            print("Table already exists")

    def insert(self, id, partition, vals):
        keys = {"PartitionKey": partition, "RowKey": id}
        entity = {**keys, **vals}
        self.table_client.create_entity(entity)

    def query(self, partition):
        result = self.table_client.query_entities(query_filter="PartitionKey eq @pk", parameters={"pk": partition})
        return result