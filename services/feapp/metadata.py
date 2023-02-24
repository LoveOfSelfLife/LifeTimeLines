# coding: utf-8

# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
    Set the environment variables with your own values before running the sample:
    1) TABLES_STORAGE_ENDPOINT_SUFFIX - the Table service account URL suffix
    2) TABLES_STORAGE_ACCOUNT_NAME - the name of the storage account
    3) TABLES_PRIMARY_STORAGE_ACCOUNT_KEY - the storage account access key
"""

from datetime import datetime, timedelta
import os
from dotenv import find_dotenv, load_dotenv
from azure.data.tables import TableClient
from azure.data.tables import TableServiceClient

class ServicesTbl(object):
    def __init__(self):
        load_dotenv(find_dotenv())
        self.access_key = os.getenv("TABLES_PRIMARY_STORAGE_ACCOUNT_KEY")
        self.endpoint_suffix = os.getenv("TABLES_STORAGE_ENDPOINT_SUFFIX")
        self.account_name = os.getenv("TABLES_STORAGE_ACCOUNT_NAME")
        self.table_name = 'ltlservicesmetatbl'
        self.connection_string = f"DefaultEndpointsProtocol=https;AccountName={self.account_name};AccountKey={self.access_key};EndpointSuffix={self.endpoint_suffix}"

    def authentication_by_connection_string(self):
        table_service = TableServiceClient.from_connection_string(conn_str=self.connection_string)

    def read_table(self):
        with TableClient.from_connection_string(self.connection_string, self.table_name) as table_client:
            try:
                entities = list(table_client.list_entities())
                return entities
            except:
                return None

if __name__ == "__main__":
    tbl = ServicesTbl()
    tbl.authentication_by_connection_string()
    entities = tbl.read_table()
    for i, entity in enumerate(entities):
        print(f"Entity #{i}: {entity}")
