from common.entity_store import EntityObject
class DriveSyncConfig (EntityObject):
    """ this table holds configurations for syncing files from google drive to azure file share
    """
    table_name='DriveSyncConfigTable'
    fields=["id",
            "version",
            "enabled",
            "sync_interval",
            "drive_path",
            "drive_path_id",
            "file_share_path",
            "default_to_sync_file_patterns"]
    key_field="id"
    partition_value="drive_sync"
    is_editable = True

    def __init__(self, d={}):
        super().__init__(d)

class TKRequestToTKZip(EntityObject):
    """ this table holds 
    """
    table_name='TKRequestToTKZipTable'
    fields=["request_id",
            "zip_filename",
            "status"]

    key_field="zip_filename"
    partition_field="request_id"

    def __init__(self, d={}):
        super().__init__(d)

class TKZipToTKDataPath(EntityObject):
    """ 
    """
    table_name='TKZipToTKDataPathTable'
    fields=["file_key, zip_filename",
            "data_file_path",
            "category",
            "file_type",
            "size",
            "compressed_size",
            "status"]

    key_field="file_key"
    partition_field="zip_filename"

    def __init__(self, d={}):
        super().__init__(d)

def extract_product_from_path(path):
    """
    a google takeout zipfiles contain a list of files in the following format:
        Takeout/<product>/<subfolders and files>...
    """
    
    path = path[1:] if path[0] == '/' else path

    parts = path.split('/')
    if len(parts) < 2:
        return None
    return parts[1]
