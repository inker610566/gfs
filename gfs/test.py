from __future__ import print_function
import httplib2
import os

from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools
from apiclient.http import MediaFileUpload

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/drive-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/drive'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Drive API Python Quickstart'


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'drive-python-quickstart.json')

    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def AcquireDriveService():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('drive', 'v3', http=http)
    return service

class Folder:
    def __init__(self, driveService, fullpath=None, idpath=None):
        '''
        :Args:
            - drive
            - fullpath: a list of folder name start from root,
                        empty list refer to root
        '''
        assert (fullpath is None) != (idpath is None)
        self.__ds = driveService
        if fullpath is not None:
            self.__idPath = ['root']
            for f in fullpath:
                fid = self.__openFromPidName(self.__idPath[-1], f)
                assert fid is not None
                self.__idPath.append(fid)
        else:
            self.__idPath= idpath

    def __openFromPidName(self, pid, name):
        '''
        :Returns:
            - pid
        '''
        response = self.__ds.files().list(
            q="'%s' in parents and name = '%s' and mimeType='application/vnd.google-apps.folder'"%(pid, name),
            fields="files(id)"
        ).execute()
        f = response.get('files', [None])[0]
        if f:
            return f.get('id')
        else:
            return None

    def List(self):
        '''
        '''
        pass

    def Create(self, name="", LocalPath="", isFolder=False):
        '''
        Create file/folder under this folder

        :Args:
            - name: str, name of created file/folder
            - LocalPath: str, if upload from local file
            - isFolder: boolean, True if folder created else file created

        :Returns:
            - Folder object or File object
        '''
        name = name or (os.path.split(LocalPath)[1] if LocalPath else "")
        assert name, "Create without filename"

        folder_id = self.__idPath[-1]
        metadata = {
          'name' : name,
          'parents': [folder_id]
        }
        http_args = {
            'body': metadata,
            'fields': 'id'
        }
        if isFolder:
            metadata['mimeType'] = 'application/vnd.google-apps.folder'
        if LocalPath and not isFolder:
            # try read LocalPath
            assert os.path.exists(LocalPath) and os.path.isfile(LocalPath)
            #http_args['media_body'] = MediaFileUpload(LocalPath, resumable=True)
            response = self.__ds.files().create(body=metadata, media_body=MediaFileUpload(LocalPath, resumable=True)).execute()
            return fid

        response = self.__ds.files().create(**http_args).execute()
        fid = response.get('id')
        return Folder(self.__ds, idpath=self.__idPath+[fid]) if isFolder else fid

    def Open(self, folderName):
        '''
        Get Folder object under current folder
        '''
        fid = self.__openFromPidName(self.__idPath[-1], folderName)
        assert fid is not None
        return Folder(self.__ds, idpath=self.__idPath+[fid])

    def Download(self, filename, LocalPath=None):
        '''
        Download file from google drive
        '''
        LocalPath = LocalPath or filename

def main():
    ds = AcquireDriveService()
    f = Folder(ds, fullpath=['tmp_folder'])
    f2 = f.Open('inner_folder')
    f2.Create(LocalPath='./test.py')


if __name__ == '__main__':
    main()
