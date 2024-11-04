from flask import (
    Flask, redirect, render_template, request, flash, jsonify, send_file, Blueprint
)
import time
import os
import requests
from common.auth_requestor import ApiTokenRequestor

main = Blueprint('be', __name__)  

@main.route("/be")
def contacts():
    return render_template("be.html")

# ===========================================================
# JSON Data API
# ===========================================================

@main.route("/api/v1/be/<info>", methods=["GET"])
def json_be(info):
    tr = ApiTokenRequestor()
    token = tr.get_token()

    # info = 'xyz'
    service = 'photos'
    path = f"/tasks/drive/look/{info}"

    URL=f'https://{service}.ltl.richkempinski.com{path}'
    headers={'Authorization': 'Bearer ' + token}
    resp = requests.get(URL, verify=False, headers=headers)

    return resp.json(), resp.status_code    

@main.route("/api/v1/be/copy/<src_file_id>/<info>", methods=["GET"])
def json_copy(src_file_id, info):
    tr = ApiTokenRequestor()
    token = tr.get_token()
    
    service = 'photos'
    # path = f"/tasks/drive/look/{info}"
    path = f"/tasks/drive/copy-incr/{src_file_id}/{info}"

    URL=f'https://{service}.ltl.richkempinski.com{path}'
    headers={'Authorization': 'Bearer ' + token}
    resp = requests.get(URL, verify=False, headers=headers)

    return resp.json(), resp.status_code    



if __name__ == "__main__":
    pass
