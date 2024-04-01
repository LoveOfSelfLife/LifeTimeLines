from azure.core import MatchConditions
from common.table_store import TableStore

class IDGenerator():
    id_table_store = None

    def __init__(self):
        pass

    @staticmethod
    def _get_table_client():
        if IDGenerator.id_table_store is None:
            IDGenerator.id_table_store = TableStore("IdTable")
        return IDGenerator.id_table_store.table_client

    @staticmethod
    def get_unique_id(namespace='id'):
        table_client = IDGenerator._get_table_client()
        # we try this 3 times in case of a conflict with another request
        for i in range(3):
            try:
                id_entity = table_client.get_entity(partition_key="id", row_key=namespace)
            except:
                # this only happens the first time when the id does not exist in the table, so we insert it with id=0
                id = 0
                table_client.upsert_entity(entity={"PartitionKey": "id", "RowKey": namespace, "id": id+1})
                return str(id)
        
            id = id_entity['id']
            etag = id_entity.metadata['etag']
            id_entity['id'] = id+1
            try:
                table_client.update_entity(mode='replace', entity=id_entity, etag=etag, match_condition=MatchConditions.IfNotModified)
                return str(id)
            except:
                continue
        raise Exception(f"Could not obtain a unique id for namespace: {namespace}")
