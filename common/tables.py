from azure.data.tables import TableClient, TableTransactionError
from azure.core.exceptions import ResourceExistsError

"""
break up a range into smaller chunks and will return an iterator of sub-ranges 
where length of each sub-range is <= chunksize
the last sub-range returned may be smaller than chunksize
"""
def divide_range_into_chunks(start, end, chunksize):
    total_len = end-start
    for b,e in [(x,x+chunksize) for x in range(0, total_len, chunksize)]:
        yield (start+b, start+e if e <= total_len else total_len)

class TableStore():
    connection_string = None

    @staticmethod
    def initialize(connection_string):
        TableStore.connection_string = connection_string

    def __init__(self, table_name:str):
        if not self.connection_string:
            raise Exception("Table connection creds null")
        self.table_client = TableClient.from_connection_string(conn_str=TableStore.connection_string, table_name=table_name)
        try:
            self.table_client.create_table()
            print("Created table")
        except ResourceExistsError:
            print("Table already exists")

    def insert(self, partition_key, row_key, vals):
        keys = {"PartitionKey": partition_key, "RowKey": row_key}
        entity = {**keys, **vals}
        self.table_client.create_entity(entity)

    def upsert(self, partition_key, row_key, vals):
        keys = {"PartitionKey": partition_key, "RowKey": row_key}
        entity = {**keys, **vals}
        self.table_client.upsert_entity(entity)

    def query(self, partition_key, filter=None):
        if filter:
            result = self.table_client.query_entities(query_filter=f"PartitionKey eq @pk and {filter}", parameters={"pk": partition_key})
        else:
            result = self.table_client.query_entities(query_filter=f"PartitionKey eq @pk", parameters={"pk": partition_key})            
        return result

    def delete_item(self, partition_key, row_key):
            self.table_client.delete_entity(partition_key=partition_key, row_key=row_key)

    def delete(self, partition_key, filter=None):
        results = self.query(partition_key, filter)
        to_delete = []
        try:
            for item in results:
                to_delete.append({"PartitionKey": partition_key, "RowKey": item['RowKey']})
            self.batch_delete(to_delete)
            return '', 204
        except:
            print("error during delete")
        return '', 404

    def batch_delete(self, entities):
        return self.batch_operation("delete", entities)

    def batch_upsert(self, entities):
        return self.batch_operation("upsert", entities)
    
    def batch_operation(self, op, entities):        
        CHUNK_SIZE=50
        elen = len(entities)
        # break up the potentially long list of entities into chunks
        for start,end in divide_range_into_chunks(0, elen, CHUNK_SIZE):
            operations = [ (op, e) for e in entities[start:end] ]
            try:
                self.table_client.submit_transaction(operations)
            except TableTransactionError as e:
                print("There was an error with the transaction operation")
                print(e)
