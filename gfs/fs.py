import os
from apiclient.http import MediaFileUpload

class GFile:
    '''
    File on google drive
    '''
    def __init__(self, driveService, file_id):
        self.__id = file_id


class GFolder:
    '''
    Folder on google drive
    '''
    def __init__(self, driveService, fullpath=None, idpath=None):
        '''
        Specified one of fullpath or idpath of drive folder, but not both.

        :Args:
            - drive
            - fullpath: a list of folder name start from root,
                        empty list refer to root
        '''
        assert (fullpath is None) != (idpath is None), "Specified either fullpath or idpath"
        self.__ds = driveService
        if idpath is None:
            idpath = ['root']
            for f in fullpath:
                fid = self.__openFromPidName(idpath[-1], f)
                assert fid is not None
                idpath += [fid]
        self.__idPath= idpath

    def __openFromPidName(self, pid, name):
        '''
        :Returns:
            - folder id if exist else None
        '''
        response = self.__ds.files().list(
            q="'%s' in parents and name = '%s' and mimeType='application/vnd.google-apps.folder'"%(pid, name),
            fields="files(id)"
        ).execute()
        f = (response.get('files') or [None])[0]
        return f and f.get('id')

    def List(self):
        '''
        :Returns:
            - (GFiles, GFolders)
        '''
        assert False

    def __prepareHttpArgs(self, name, isFolder, LocalPath=""):
        metadata = {
          'name' : name,
          'parents': [self.__idPath[-1]]
        }
        http_args = {
            'body': metadata,
            'fields': 'id'
        }
        if isFolder:
            metadata['mimeType'] = 'application/vnd.google-apps.folder'
        if LocalPath:
            assert os.path.exists(LocalPath) and os.path.isfile(LocalPath)
            http_args['media_body'] = MediaFileUpload(LocalPath, resumable=True)
        return http_args

    def Upload(self, LocalPath, name="", progressCallback=None):
        '''
        Upload file to GFolder

        :Args:
            - LocalPath: str, path to upload file on local file system
            - name: str, upload name
            - progressCallback: callable, call with upload progress(percent) argument
        '''
        name = name or (os.path.split(LocalPath)[1] if LocalPath else "")

        http_args = self.__prepareHttpArgs(name, False, LocalPath)
        request = self.__ds.files().create(**http_args)

        response = None
        while response is None:
            status, response = request.next_chunk()
            if progressCallback and status:
                progressCallback(status.progress()*100)

    def Create(self, name, isFolder=False):
        '''
        Create file/folder under this folder

        :Args:
            - name: str, name of created file/folder
            - isFolder: boolean, True if folder created else file created

        :Returns:
            - GFolder object or GFile object
        '''
        http_args = self.__prepareHttpArgs(name, isFolder)
        response = self.__ds.files().create(**http_args).execute()
        fid = response.get('id')
        if isFolder:
            return GFolder(self.__ds, idpath=self.__idPath+[fid])
        else:
            return GFile(self.__ds, fid)

    def Open(self, folderName):
        '''
        Get GFolder object under current folder
        
        :Returns:
            - GFolder if exists else None
        '''
        fid = self.__openFromPidName(self.__idPath[-1], folderName)
        return fid and GFolder(self.__ds, idpath=self.__idPath+[fid])

    def Download(self, filename, LocalPath=None):
        '''
        Download file from google drive
        '''
        LocalPath = LocalPath or filename
        assert False
