from googleapiclient.discovery import build
from common.google_credentials import get_credentials


class GoogleDrive:
    """
    A class to interact with Google Drive using the Google Drive API.
    """

    def __init__(self):
        """
        Initializes the GoogleDrive instance and sets up the service.
        """
        from googleapiclient.discovery import build
        self.service = build('drive', 'v3', credentials=get_credentials())

    def get_drive_service(self):
        """
        Returns the Google Drive service instance.

        Returns:
            googleapiclient.discovery.Resource: The Google Drive service instance.
        """
        return self.service
    
    def get_file_info(self, file_id):
        """
        Retrieves information about a file given its file ID.

        Args:
            file_id (str): The ID of the file.

        Returns:
            dict: A dictionary containing the file information.
        """
        return self.service.files().get(fileId=file_id).execute()

    def get_file_name_from_id(self, file_id):
        """
        Retrieves the name of a file given its file ID.

        Args:
            file_id (str): The ID of the file.

        Returns:
            str: The name of the file.
        """
        return self.service.files().get(fileId=file_id).execute()['name']
    
    def get_file_id_from_name(self, filename):
        """
        Retrieves the ID of a file given its name.

        Args:
            filename (str): The name of the file.

        Returns:
            str or None: The ID of the file if found, otherwise None.
        """
        ids = self.get_file_ids_from_name(filename)
        if ids:
            return ids[0]['id']
        return None

    def get_file_ids_from_name(self, filename):
        """
        Retrieves the IDs of files given their name.

        Args:
            filename (str): The name of the files.

        Returns:
            list: A list of dictionaries containing the file IDs and names.
        """
        query=f"name = '{filename}' and trashed=false"
        results = self.service.files().list(
            q=query,
            fields="files(id, name)").execute()
        items = results.get('files', [])
        if items:
            return items
        return None
    
    def list_files_in_folder_with_id(self, folder_id, filename=None, partial_match=True):
        """
        Lists files in a folder given the folder ID.

        Args:
            folder_id (str): The ID of the folder.
            filename (str, optional): The name of the file to filter by. Defaults to None.
            partial_match (bool, optional): Whether to use partial match for the filename. Defaults to True.

        Yields:
            dict: A dictionary containing the file information.
        """
        query=f"'{folder_id}' in parents and trashed=false"
        if filename:
            if partial_match:
                query += f" and name contains '{filename}'"
            else:
                query += f" and name = '{filename}'"
        yield from self._list_files(query)

    def list_files_in_folder_with_name(self, folder_name, filename=None, partial_match=True):
        """
        Lists files in a folder given the folder name.

        Args:
            folder_name (str): The name of the folder.
            filename (str, optional): The name of the file to filter by. Defaults to None.
            partial_match (bool, optional): Whether to use partial match for the filename. Defaults to True.

        Yields:
            dict: A dictionary containing the file information.
        """
        folder_id = self.get_file_id_from_name(folder_name)
        yield from self.list_files_in_folder_with_id(folder_id, filename, partial_match)

    def _list_files(self, query):
        """
        Helper method to list files based on a query.

        Args:
            query (str): The query string to filter files.

        Yields:
            dict: A dictionary containing the file information.
        """
        page_token = None
        while True:
            results = self.service.files().list(
                pageToken=page_token,
                q=query,
                fields="files(id, name, mimeType, createdTime, modifiedTime, size), nextPageToken"
                ).execute()
            for item in results.get('files', []):
                yield item
            page_token = results.get('nextPageToken', None)
            if not page_token:
                break
