import os
from dotenv import find_dotenv, load_dotenv

class CreateClients(object):
    def __init__(self):
        load_dotenv(find_dotenv())
        self.connection_string = os.getenv("AZURE_STORAGETABLE_CONNECTIONSTRING")
        self.table_name = "sampleTransaction"

    def sample_transaction(self):
        # Instantiate a TableClient using a connection string
        entity1 = {"PartitionKey": "pk001", "RowKey": "rk001", "Value": 4, "day": "Monday", "float": 4.003}
        entity2 = {"PartitionKey": "pk001", "RowKey": "rk002", "Value": 4, "day": "Tuesday", "float": 4.003}
        entity3 = {"PartitionKey": "pk001", "RowKey": "rk003", "Value": 4, "day": "Wednesday", "float": 4.003}
        entity4 = {"PartitionKey": "pk001", "RowKey": "rk004", "Value": 4, "day": "Thursday", "float": 4.003}

        # [START batching]
        from azure.data.tables import TableClient, TableTransactionError
        from azure.core.exceptions import ResourceExistsError

        self.table_client = TableClient.from_connection_string(
            conn_str=self.connection_string, table_name=self.table_name
        )

        try:
            self.table_client.create_table()
            print("Created table")
        except ResourceExistsError:
            print("Table already exists")

        self.table_client.upsert_entity(entity2)
        self.table_client.upsert_entity(entity3)
        self.table_client.upsert_entity(entity4)

        operations = [
            ("upsert", entity1),
            ("delete", entity2),
            ("upsert", entity3),
            ("update", entity4, {"mode": "replace"}),
        ]
        try:
            self.table_client.submit_transaction(operations) # type: ignore[arg-type]
        except TableTransactionError as e:
            print("There was an error with the transaction operation")
            print(e)
        # [END batching]

    def clean_up(self):
        print('cleanup')
        self.table_client.delete_table()
        self.table_client.__exit__()


if __name__ == "__main__":
    sample = CreateClients()
    try:
        print('before sample transaction')
        sample.sample_transaction()
        print('after sample transaction')
    finally:
        sample.clean_up()
