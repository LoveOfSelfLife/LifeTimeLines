import zipfile
import json

def zip_crawl(path_to_zipfile):
    json_files_list = []
    non_json_files_list = []
    with zipfile.ZipFile(path_to_zipfile, 'r') as zip_ref:
        names = zip_ref.namelist()
        for name in names:
            if name.endswith('.json'):
                json_files_list.append(name)
            else:
                non_json_files_list.append(name)
    return json_files_list, non_json_files_list

def zip_json_extractor(path_to_zipfile, json_files_list):
    json_list = []
    with zipfile.ZipFile(path_to_zipfile, 'r') as zip_ref:
        for name in json_files_list:
            with zip_ref.open(name) as json_file:
                inner_json = json.load(json_file)
                extracted_json = { "name" : name, "json" : inner_json }
                json_list.append(extracted_json)
    return json_list
