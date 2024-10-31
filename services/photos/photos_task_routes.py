from flask_restx import Namespace, Resource, reqparse, fields
from flask import request, url_for, redirect
import requests
import datetime
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from common.jwt_auth import AuthError
from googlephotosapi import GooglePhotosApi
from common.google_credentials import GOOGLE_SCOPES, get_config_from_secret, get_credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from photos_sync import PhotosSyncMgr
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from io import BytesIO
import zipfile

from photos_tasks import PHOTOS_TASKS

ns = Namespace('tasks', description='services to sync with google photos')

def is_task(task):
    return next((x for x in PHOTOS_TASKS if x['task_name'] == task), None)

@ns.route('/')
class PhotosTasks(Resource):

    '''Shows all photos tasks '''
    @ns.doc('list tasks')
    def get(self):
        '''List all tasks '''
        return [ t['task_name'] for t in PHOTOS_TASKS ]

@ns.route('/<task>')
@ns.response(404, 'Operation not found')
@ns.param('task', 'The specific identifier')
class PhotosTasksOperations(Resource):

    @ns.doc('get list of task instances created for a specific task')
    def get(self, task):
        # if task == 'status':
        #     return [{"gap": "gap"}, {"gap": "gap"}]
        # elif is_task(task):

        if is_task(task):
            return [ { "task": f"{task}", "id": 101, "status" : "completed"}, 
                     { "task": f"{task}", "id": 102, "status" : "processing"}
                    ]
        else:
            return 'unknown task', 404
    
    def post(self, task):
        '''create a specific instance of task '''
        # sm = PhotosSyncMgr()
        # result = sm.update_operation(id, ns.payload)
        # return result, 204
        if is_task(task):
            return {'result': f'result-value: {task}', 'id': 103}
        else:
            return 'unknown task', 404

@ns.route('/<task>/<id>')
@ns.response(404, 'Operation not found')
@ns.param('task', 'The specific task')
@ns.param('id', 'The specific task ID')
class PhotosTaskInstances(Resource):

    @ns.doc('get list of task instances')
    def get(self, task, id):
        if is_task(task):
            return [ { "task": f"{task}", "id": f"{id}", "status" : "commpleted"}]
        else:
            return 'unknown task', 404
    
    def put(self, task, id):
        '''create a specific instance of task '''
        # sm = PhotosSyncMgr()
        # result = sm.update_operation(id, ns.payload)
        # return result, 204
        if is_task(task):
            return {'result': f'result-value: {task}', 'id': f"{id}"}

    @ns.doc('delete sync operation')
    @ns.response(204, 'Operation deleted')
    def delete(self, task, id):
        '''Delete an instance of a task given its id'''
        # sm = PhotosSyncMgr()
        # sm.del_operation(id)
        return f'{id}', 204

def get_files(name):
    try:
        service = build("drive", "v3", credentials=get_credentials())

        # Call the Drive v3 API
        results = (
            service.files()
            .list(pageSize=50,
                    # q="mimeType='image/jpeg'",
                    q=f"name contains '{name}'",
                    spaces="drive",
                    fields="nextPageToken, files(id, name)",
                    pageToken=None)
            .execute()
        )
        
        items = results.get("files", [])

        if not items:
            return {"status": "No files found."}
        
        files_list = []
        for item in items:
            files_list.append({"name": item["name"], "id": item["id"]})
        return { "files" : files_list }

    except HttpError as error:
        return {"status": f"error occurred {error}"}, 500
        
def unzipfile(file_id):

    try:
        service = build("drive", "v3", credentials=get_credentials())

        request = service.files().get_media(fileId=file_id)
        fh = BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()

        # Unzip in memory
        fh.seek(0)
        with zipfile.ZipFile(fh, 'r') as zip_ref:
            # Extract all files (optional)
            # zip_ref.extractall()
            return { "files" :  zip_ref.namelist() }

            # Read a specific file from the zip
            # with zip_ref.open('path/to/file/in/zip.txt') as f:
            #     content = f.read()
            #     print(content.decode('utf-8'))
    except:
        return {"status":"error occurred"}, 500

@ns.route('/drive/<file_id>')
class PhotosTaskInstances(Resource):

    @ns.doc('get file from google')
    def get(self, file_id):
        '''get file from google drive'''
        return unzipfile(file_id)
        # return get_files(file_id)
        

copy_fields = ns.model('Resource', {
    'file_id': fields.String,
    'destination': fields.String
})

def copy_drive_file(service, src_file_id, dst_folder_file, token):
    # file = service.files().get(fileId=src_file_id, fields='name, mimeType, webContentLink, exportLinks').execute()
    # download_url = file.get('webContentLink')
    download_url = f"https://www.googleapis.com/drive/v3/files/{src_file_id}?alt=media"
    headers = {'Authorization': 'Bearer ' + token}
    response = requests.get(download_url, stream=True, allow_redirects=True, headers=headers)
                                                                                      
    with open(dst_folder_file, 'wb') as f:
        for chunk in response.iter_content(1024):
            f.write(chunk)

@ns.route('/drive/copy/<file_id>')
class CopyDriveFiles(Resource):

    @ns.doc('copy file from google to file store')
    @ns.expect(copy_fields)
    def post(self):
        json_data = request.get_json(force=True)
        file_id = json_data['file_id']
        destination = json_data['destination']

        return { "file_id": file_id, "destination": destination }

@ns.route('/drive/look/<info>')
class LsFiles(Resource):
    @ns.doc('look at file store')
    def get(self, info):
        import os
        newdir = info.replace("_", "/")
        file_info = os.listdir(newdir)
        return { "info":info, "cwd": os.getcwd(), "file_info": file_info }

@ns.route('/drive/copy/<src_file_id>/<info>')
class CopyFiles(Resource):
    @ns.doc('coppy file from drive')
    def get(self, src_file_id, info):
        import os
        import time
        from google.auth.transport.requests import Request
        dst_folder_file = info.replace("_", "/")
        credentials=get_credentials()
        credentials.refresh(Request())
        # service = build("drive", "v3", credentials=credentials)
        start_time = time.time()
        copy_drive_file(None, src_file_id, dst_folder_file, credentials.token)
        end_time = time.time()
        return { "dest":dst_folder_file, "time": end_time - start_time }
        


