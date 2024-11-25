
import logging
from common.share_client import FShareService, copy_file_incremental         
from common.google_drive import GoogleDrive

def copy_drive_file_to_fileshare_fn(drive_file_id, fileshare_path, token=None, instance_id=None):
    logging.info(f"copy_drive_file_to_fileshare_fn(file_id={drive_file_id}, fileshare_path={fileshare_path})")
    drive = GoogleDrive()
    file_share_service = FShareService()

    copy_file_incremental(drive, file_share_service, drive_file_id, fileshare_path, str(instance_id))
                          
    return (f"copy_drive_file_to_fileshare_fn(file_id={drive_file_id}, fileshare_path={fileshare_path}, instance_id={instance_id})", 200)

