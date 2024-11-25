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
