import os
import string
import requests
import logging

def send_internal_request(container_app, auth_token=None):

    logger = logging.getLogger(__name__)

    # 1. Use the target Container App's name as the hostname
    # 2. Traffic is sent over HTTP (port 80) within the environment
    target_app_name = container_app
    url = f"http://{target_app_name}/sys/test-job-run"
    

    # Retrieve your secured token (ideally injected via environment variables)
    if not auth_token:
        auth_token = os.environ.get("INTERNAL_API_TOKEN", "your_secret_token_here")
    
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "message": "Hello from the frontend app!",
        "status": "pending"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, verify=False, timeout=5)
        response.raise_for_status()
        response_string = str(response.text)
        logger.info(f"Success: {response_string[:100]}")
        return response_string
    except requests.exceptions.RequestException as e:
        logger.error("Internal communication failed:", exc_info=e)
        return None
