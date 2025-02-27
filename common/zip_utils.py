import zipfile
import json

def zip_extract_filenames(path_to_zipfile, suffix_list=['.json']):
    json_files_list = []
    non_json_files_list = []
    files_dict = {}
    with zipfile.ZipFile(path_to_zipfile, 'r') as zip_ref:
        names = zip_ref.namelist()
        for name in names:
            found_suffix = False
            for suffix in suffix_list:
                if name.lower().endswith(suffix.lower()):
                    files_dict[suffix] = files_dict.get(suffix, []) + [name]
                    found_suffix = True
                    break
            if not found_suffix:
                files_dict['other'] = files_dict.get('other', []) + [name]
    return files_dict

def zip_extract_file_details(path_to_zipfile):
    files_dict = {}
    files_list = []
    with zipfile.ZipFile(path_to_zipfile, 'r') as zip_ref:
        names = zip_ref.namelist()
        for name in names:
            finfo = {}
            file_info = zip_ref.getinfo(name)
            finfo['name'] = name
            finfo['size'] = file_info.file_size
            finfo['compress_size'] = file_info.compress_size
            finfo['date_time'] = file_info.date_time
            files_list.append(finfo)
    return files_list

def zip_json_file_extractor(path_to_zipfile, json_files_list):
    json_list = []
    with zipfile.ZipFile(path_to_zipfile, 'r') as zip_ref:
        for name in json_files_list:
            with zip_ref.open(name) as json_file:
                inner_json = json.load(json_file)
                extracted_json = { "name" : name, "json" : inner_json }
                json_list.append(extracted_json)
    return json_list
    
from common.entity_store import  EntityStore, EntityObject
from common.env_context import Env
    
class TakeoutPhotosIndex (EntityObject):
    """ this table 
    """
    table_name='TakeoutPhotosIndexTable'
    fields=["basename", "takeout_id", "json_filename", "non_json_filename"]
    key_field="basename"
    partition_field="takeout_id"

    def __init__(self, d={}):
        super().__init__(d)

    """
    a google takeout zipfiles contain a list of files in the following format:
        Takeout/<product>/<subfolders and files>...
    for example:
        Takeout/Google Photos/Rich_K_Photos_Album/10111.jpg
    the zip file contains a list of files that are extracted from the google takeout
    the files are extracted into the product folder

    the goal of this function is to:
    1. extract the list of file names from a zip file
    2. separate the lists into different product lists, then handle each list based on the product
    For Google Photos, the files are eihter json files or image files
    there should be one json file for each image file

    as the filenames in each google photos is processed, we create an object for that filename and store 
    that object into the entity store
    The ID of the Takeout operation will be the partition key for the object
    The filename sans it's suffix will be the key for the object
    the attributes will be the full filename of the json file with a json_suffix, and the filename of the file without the json_suffix




    """