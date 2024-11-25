
import logging
from common.zip_utils import zip_extract_filenames, zip_json_extractor, TakeoutPhotosIndex
from common.entity_store import EntityStore
import json

def basename(path):
    return ''.join(path.split('.')[0:-1])

def zip_crawler(path_to_zipfile, takeout_id, token=None, instance_id=None):
    logging.info(f"Starting zip_crawler(path_to_zipfile={path_to_zipfile})")
    try:
        filenames_dict = zip_extract_filenames(path_to_zipfile, suffix_list=['.json'])
        json_file_names = filenames_dict.get('.json', [])
        non_json_file_names = filenames_dict.get('other', [])
        es = EntityStore()

        takeout_json_index = [ TakeoutPhotosIndex({"basename": basename(name), "takeout_id": takeout_id, "json_filename": name}) for name in json_file_names ]
        es.upset_items(takeout_json_index)

        takeout_non_json_index = [ TakeoutPhotosIndex({"basename": basename(name), "takeout_id": takeout_id, "non_json_filename": name}) for name in non_json_file_names ]
        es.upset_items(takeout_non_json_index)

    except Exception as e:
        logging.exception(f"Error occurred during zip_crawler: {e}")
        raise Exception(f"Error occurred during zip_crawler: {e}")

    logging.info(f"Completed zip_crawler(path_to_zipfile={path_to_zipfile})")
    return(f"Finished zip_crawler(path_to_zipfile={path_to_zipfile}, {output_file})")
