
import logging
from common.zipper import zip_crawl, zip_json_extractor
import json

def zip_crawler(path_to_zipfile, output_file, token=None, instance_id=None):
    logging.info(f"Starting zip_crawler(path_to_zipfile={path_to_zipfile})")
    try:
        json_file_names, non_json_file_names = zip_crawl(path_to_zipfile)

        with open(output_file, 'w') as f:
            for jname in json_file_names:
                f.write(f"{jname}\n")

        # json_list = zip_json_extractor(path_to_zipfile, json_file_names)
        # n=0
        # with open(output_file, 'w') as f:
        #     for item in json_list:
        #         logging.info(f"processing file #{n}: {item}")
        #         f.write('[\n' if n==0 else ',\n')
        #         n += 1
        #         f.write(f"{json.dumps(item, indent=4)}")
        #     f.write(']\n')
    except Exception as e:
        logging.exception(f"Error occurred during zip_crawler: {e}")
        raise Exception(f"Error occurred during zip_crawler: {e}")

    logging.info(f"Completed zip_crawler(path_to_zipfile={path_to_zipfile})")
    return(f"Finished zip_crawler(path_to_zipfile={path_to_zipfile}, {output_file})")
