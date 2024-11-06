import os
import time
from googleapiclient.discovery import build

from azure.storage.fileshare import ShareClient, ShareFileClient
from requests.exceptions import RequestException
from common.entity_store import EntityObject, EntityStore
from common.env_context import Env

from common.jwt_auth import AuthError

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from common.google_credentials import GOOGLE_SCOPES, get_config_from_secret, get_credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.http import MediaIoBaseDownload
from google.auth.transport.requests import Request
import logging

DEFAULT_SHARE_NAME = 'richkhome'

class GoogleDrive:

    def __init__(self):
        self.service = build('drive', 'v3', credentials=get_credentials())

    def get_drive_service(self):
        return self.service
    
class FShareService: 
    connection_string = None

    @staticmethod
    def initialize(connection_string:str):
        FShareService.connection_string = connection_string

    def __init__(self, share_name:str = DEFAULT_SHARE_NAME):
        self.client = ShareClient.from_connection_string(FShareService.connection_string, share_name=share_name)
    
    def getFShareFileClient(self, filepath:str):
        return self.client.get_file_client(filepath)

class FileCopyProgress (EntityObject):
    table_name="FileCopyProgressTable"
    fields=["operation_id", "offset"]
    key_field="offset"
    partition_field="operation_id"

    def __init__(self, d={}):
        super().__init__(d)

def copy_file_incremental(drive:GoogleDrive, file_share_service:FShareService, 
                          src_drive_file_id:str, dest_fileshare_path:str, operation_id:str):

    logging.info(f"Copying file {src_drive_file_id} to {dest_fileshare_path} incrementally")

    try:
        drive_service = drive.get_drive_service()
        dest_file_client= file_share_service.getFShareFileClient(dest_fileshare_path)
        # dest_file_client= ShareFileClient.from_connection_string(FShareService.connection_string, 
        #                                                          share_name='richkhome',
        #                                                          file_path=dest_fileshare_path)

        chunk_size=4 * 1024 * 1024

        src_file_metadata = drive_service.files().get(fileId=src_drive_file_id, fields='size').execute()
        src_file_size = int(src_file_metadata['size'])

        # Initialize file in Azure with the target file size
        dest_file_client.create_file(size=src_file_size)

        entity_store = EntityStore()
        progress_items = entity_store.list_items(FileCopyProgress({"operation_id": operation_id}))    
        num_completed_offsets = len(list(progress_items))
        
        start_offset = 0
        retry_count = 0
        while start_offset < src_file_size:
            end_offset = min(start_offset + chunk_size, src_file_size) - 1

            check_point = FileCopyProgress({"operation_id": str(operation_id), "offset": str(start_offset)})
            if entity_store.get_item(check_point) is None:  # Skip if already uploaded
                try:
                    chunk_data = download_chunk(drive_service, src_drive_file_id, start_offset, end_offset)
                    length=len(chunk_data)
                    dest_file_client.upload_range(data=chunk_data, offset=start_offset, length=length)

                    # Save checkpoint in progress table
                    entity_store.upsert_item(check_point, track_last_updated_item=False)
                    num_completed_offsets += 1
                    retry_count = 0  # Reset retry count on success

                except RequestException as e:
                    print(f"Retrying upload for offset {start_offset} due to error: {e}")
                    retry_count += 1
                    if retry_count > 5:
                        print(f"Failed to upload chunk at offset {start_offset} after 5 retries. Aborting.")
                        break
                    time.sleep(2 ** (len(num_completed_offsets) % 5))  # Exponential backoff

            start_offset += chunk_size

        if start_offset >= src_file_size:
            print(f"Completed {num_completed_offsets} offsets. we are done, we should now delete the progress items")
            # entity_store.delete_items(FileCopyProgress({"operation_id": operation_id}))
            return True
        else:
            print(f"Completed {num_completed_offsets} offsets but not finished. - should keep the progress items")
            return False
    except Exception as e:
        logging.exception(f"Error occurred during file copy: {e}")
        return False
    
def download_chunk(drive_service, file_id, start, end):
    request = drive_service.files().get_media(fileId=file_id)
    request.headers['Range'] = f'bytes={start}-{end}'
    return request.execute()
