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
        self.table_name = table_name
        try:
            self.table_client.create_table()
            print("Created table")
        except ResourceExistsError:
            print("Table already exists")

    def insert(self, partition_key, row_key, vals):
        keys = {"PartitionKey": partition_key, "RowKey": str(row_key)}
        entity = {**keys, **vals}
        return self.table_client.create_entity(entity)

    def upsert(self, partition_key, row_key, vals):
        keys = {"PartitionKey": partition_key, "RowKey": str(row_key)}
        entity = {**keys, **vals}
        return self.table_client.upsert_entity(entity)

    def query(self, partition_value=None, filter=None, dfilter=None, select=None, start_time_iso=None, end_time_iso=None, 
              include_start_time=False, include_end_time=True):
        import datetime
        from datetime import timedelta
        start_ts = (datetime.datetime.fromisoformat(str(start_time_iso))+timedelta(microseconds=1)).strftime("%Y-%m-%dT%H:%M:%S.%f")[:] + 'Z' if start_time_iso else None
        end_ts = (datetime.datetime.fromisoformat(str(end_time_iso))+timedelta(microseconds=1)).strftime("%Y-%m-%dT%H:%M:%S.%f")[:] + 'Z' if end_time_iso else None
        start_rel = "ge" if include_start_time else "gt"
        end_rel = "le" if include_end_time else "lt"
        ts_filter = f" and (Timestamp {start_rel} datetime'{start_ts}')" if start_ts else ""
        ts_filter = f"{ts_filter} and (Timestamp {end_rel} datetime'{end_ts}')" if end_ts else ts_filter

        if partition_value:
            if filter:
                if select:
                    result = self.table_client.query_entities(query_filter=f"PartitionKey eq @pk and {filter} {ts_filter}", parameters={"pk": partition_value}, select=select)
                else:
                    result = self.table_client.query_entities(query_filter=f"PartitionKey eq @pk and {filter} {ts_filter}", parameters={"pk": partition_value})
            else:
                qfilter = f"PartitionKey eq @pk{ts_filter}"
                if select:
                    result = self.table_client.query_entities(query_filter=qfilter, parameters={"pk": partition_value}, select=select)
                else:
                    result = self.table_client.query_entities(query_filter=qfilter, parameters={"pk": partition_value})            
            return result
        else:
            # TODO: fix this to be DRY, this is just temporary
            if filter and ts_filter:
                filter = f"({filter}){ts_filter}"
            elif filter:
                filter = filter
            elif ts_filter:
                filter = f"true{ts_filter}"
            else:
                filter = ""
            if select:
                result = self.table_client.query_entities(query_filter=f"{filter}", select=select)
            else:
                print(f"table={self.table_name}, query_filter={filter}")
                result = self.table_client.query_entities(query_filter=f"{filter}")
            return result

    def parameters_to_query_string(self, filter_dict=None):
        if filter_dict:
            filter = " and ".join([f"{k} eq @{k}" for k in filter_dict.keys()])
            print(f"filter={filter}")
            return filter
        return ""
    
    def _get_time_filter(self, start_time_iso=None, end_time_iso=None, include_start_time=False, include_end_time=True):
        import datetime
        from datetime import timedelta
        start_ts = (datetime.datetime.fromisoformat(str(start_time_iso))+timedelta(microseconds=1)).strftime("%Y-%m-%dT%H:%M:%S.%f")[:] + 'Z' if start_time_iso else None
        end_ts = (datetime.datetime.fromisoformat(str(end_time_iso))+timedelta(microseconds=1)).strftime("%Y-%m-%dT%H:%M:%S.%f")[:] + 'Z' if end_time_iso else None
        start_rel = "ge" if include_start_time else "gt"
        end_rel = "le" if include_end_time else "lt"
        ts_filter = f" and (Timestamp {start_rel} datetime'{start_ts}')" if start_ts else ""
        ts_filter = f"{ts_filter} and (Timestamp {end_rel} datetime'{end_ts}')" if end_ts else ts_filter
        return ts_filter
    
    def query2(self, dfilter=None, select=None, start_time_iso=None, end_time_iso=None, 
              include_start_time=False, include_end_time=True):
        ts_filter = self._get_time_filter(start_time_iso, end_time_iso, include_start_time, include_end_time)
        from common.entity_filter import create_filter_and_params
        filter, params = create_filter_and_params(dfilter)
        if filter:
            filter = f"{filter}{ts_filter}"
        else:
            filter = ts_filter

        print(f"table={self.table_name}, query_filter='{filter}', params={params}")
        # result = self.table_client.query_entities(query_filter=filter, parameters=params, select=select)
        result = self.table_client.query_entities(query_filter=filter, parameters=params)

        return result

    def get_item(self, partition_key_value, row_key_value):
            return self.table_client.get_entity(partition_key=partition_key_value, row_key=str(row_key_value))

    def delete_item(self, partition_key, row_key):
            self.table_client.delete_entity(partition_key=partition_key, row_key=str(row_key))

    def delete_all(self):
            self.table_client.delete_table()
            print("Deleted table")
            self.table_client.create_table()
            print("Created table")
            
    def delete(self, partition_value, filter=None):
        results = self.query(partition_value, filter=filter)
        to_delete = []
        try:
            for item in results:
                to_delete.append({"PartitionKey": partition_value, "RowKey": str(item['RowKey'])})
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
        first_item = None
        last_item = None

        elen = len(entities)
        # break up the potentially long list of entities into chunks
        for start,end in divide_range_into_chunks(0, elen, CHUNK_SIZE):
            operations = [ (op, e) for e in entities[start:end] ]
            try:
                mapping_list = self.table_client.submit_transaction(operations)
                first_item = mapping_list[0] if not first_item else first_item
                last_item = mapping_list[-1]
            except TableTransactionError as e:
                print("There was an error with the transaction operation")
                print(e)
        return first_item, last_item
    