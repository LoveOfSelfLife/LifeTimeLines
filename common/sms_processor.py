import base64
import json

def process_sms_message(msg_data, auth_token):
    pass
def parse_sms_message(content):
    import requests
    import sys
    # decoding the content
    decoded_content = base64.b64decode(content).decode('utf-8')
    # parsing the json content
    parsed_content = json.loads(decoded_content)    
    return parsed_content
