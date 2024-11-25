
import os
from dotenv import load_dotenv
import unittest
import json
from common.entity_store import EntityStore
from common.env_init import initialize_environment
from common.table_store import TableStore
from common.share_client import FShareService, copy_file_incremental 
from common.google_drive import GoogleDrive        



class TestDrive(unittest.TestCase):

    def setUp(self) -> None:
        print(f"setUp()")
        load_dotenv('test/.env')
        initialize_environment()
        print(f"{os.getcwd()}")
    
    def test_google_drive(self):
        print(f"test_google_drive")
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

if __name__ == '__main__':
    unittest.main()
