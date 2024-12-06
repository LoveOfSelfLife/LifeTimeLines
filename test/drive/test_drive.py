
import os
from dotenv import load_dotenv
import unittest
import json
import hashlib
from common.entity_store import EntityStore
from common.env_init import initialize_environment
from common.table_store import TableStore
from common.share_client import FShareService, copy_file_incremental 
from common.google_drive import GoogleDrive        
from common.configs import DriveSyncConfig, TKRequestToTKZip, TKZipToTKDataPath, extract_product_from_path
from common.zip_utils import zip_extract_file_details


class TestDrive(unittest.TestCase):

    def setUp(self) -> None:
        print(f"setUp()")
        load_dotenv('test/.env')
        initialize_environment()
        print(f"{os.getcwd()}")
    
    def test_google_drive(self):
        print(f"test_google_drive")
        return
        drive = GoogleDrive()
        filename = 'stratrix-2021_10_04_14_05_50.mp3'
        foldername = 'Food Ontology'
        file_id = '1eQkvozwHPpmGRE4buDJZe4JdV58T3Tss'
        folder_id = '1hhfnPbEXRPqiFR5l_muPPlxjdV8oYE09AIYecQrolD_2zSYAGhDAGliI48Un4y0HDybzZjMe'
        partial_file_name = 'takeout-20241029T171330Z-012'

        print(f"drive.get_file_info({folder_id}): {drive.get_file_info(folder_id)}")
        print(f"drive.get_file_name({folder_id}): {drive.get_file_name_from_id(folder_id)}")
        print(f"drive.get_file_id({filename}): {drive.get_file_id_from_name(filename)}")
        print(f"drive.get_file_ids({foldername}): {drive.get_file_ids_from_name(foldername)}")
        
        print(f"drive.list_files_in_folder({foldername}):")
        for item in drive.list_files_in_folder_with_name(foldername):
            print(f"\t{item}")
        
        print(f"drive.list_files_in_folder_id({folder_id}):")
        n = 0
        for item in drive.list_files_in_folder_with_id(folder_id):
            print(f"\t{item}")
            n += 1
            if n > 10:
                break
        full_filename = 'takeout-20241029T171330Z-002.zip'
        partial_filename = 'takeout-20241029T171330Z'
        
        print(f"drive.list_files_in_folder_name({folder_id}, {full_filename}):")
        n = 0
        for item in drive.list_files_in_folder_with_id(folder_id, full_filename):
            print(f"\t{item}")
            n += 1
            if n > 10:
                break
        print(f"drive.list_files_in_folder_name({folder_id}, {partial_filename}):")
        n = 0
        for item in drive.list_files_in_folder_with_id(folder_id, partial_filename):
            print(f"\t{item}")
            n += 1
            if n > 10:
                break
        
        takeout = 'takeout-20241102T215210Z'
        takeout_files = drive.list_files_in_folder_with_id(folder_id, takeout)
        tof = list(takeout_files)
        tof.sort(key=lambda x: x['name'])
        print(f"len(takeout_files): {len(tof)}")
        for item in tof:
            print(f"\t{item}")

        self.assertTrue(True)

    def test_drive2(self):
        print(f"test_drive2")
        drive_sync = DriveSyncConfig()
        es = EntityStore()
        drive_sync_list = es.list_items(drive_sync)
        # print(f"drive_sync_list: {list(drive_sync_list)}")
        for ds in drive_sync_list:
            # print(f"{ds}")
            if ds['id'] == 'sync_takeout':
                # print(f"\t{ds}")
                drive_path_id = ds['drive_path_id']
                drive_path = ds['drive_path']
                sync_file_patterns = ds['default_to_sync_file_patterns']
                print(f"\tdrive_path_id: {drive_path_id}")
                print(f"\tdrive_path: {drive_path}")
                print(f"\tsync_file_patterns: {sync_file_patterns}")
        
        drive = GoogleDrive()
        sync_file_patterns = 'takeout-20241102T215210Z'
        drive_files = drive.list_files_in_folder_with_id(folder_id=drive_path_id
                                                         , filename=sync_file_patterns
                                                        , partial_match=True)
        sync_files = list()
        for file in drive_files:
            print(f"\t{file}")
            
            params = {  
                "request_id": sync_file_patterns,
                "zip_filename": file['name'],
                "status": "initial" }
            sync_files.append(TKRequestToTKZip(params))

        # es.upsert_items(sync_files)
        path_to_zipfile="C:/Users/richk/Downloads/takeout-20241029T015158Z-005.zip"
        files_in_zip = zip_extract_file_details(path_to_zipfile=path_to_zipfile)
        zip_paths = list()
        for f in files_in_zip:
            key = to_azure_key_string(f['name'])
            product = extract_product_from_path(f['name'])
            file_type = f['name'].split('.')[-1]
            z  = TKZipToTKDataPath({"zip_filename": "takeout-20241029T015158Z-005.zip"
                            , "file_key": key
                            , "data_file_path": f['name']
                            , "size": f['size']
                            , "category": product
                            , "file_type": str.lower(file_type)
                            , "compressed_size": f['compress_size']
                            , "status": "initial"})
            zip_paths.append(z)

        es.upsert_items(zip_paths)
        self.assertTrue(True)

def to_azure_key_string(s: str) -> str:
    return ''.join(
        c for c in s
        if c not in {'/', '\\', '#', '?', ' '} and not (ord(c) < 32 or ord(c) == 127)
    )



def create_id(data):
    """Creates a unique ID using SHA-256 hash function."""

    # Convert data to bytes if it's not already
    if not isinstance(data, bytes):
        data = str(data).encode('utf-8')

    # Create a SHA-256 hash object
    hash_object = hashlib.sha256(data)

    # Return the hexadecimal representation of the hash
    return hash_object.hexdigest()

if __name__ == '__main__':
    unittest.main()
