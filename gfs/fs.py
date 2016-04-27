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
        :Returns:
            - (GFiles, GFolders)
        '''
        assert False

    def Create(self, name="", LocalPath="", isFolder=False):
        '''
        Create file/folder under this folder

        :Args:
            - name: str, name of created file/folder
            - LocalPath: str, if upload from local file
            - isFolder: boolean, True if folder created else file created

        :Returns:
            - GFolder object or GFile object
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
            http_args['media_body'] = MediaFileUpload(LocalPath, resumable=True)

        response = self.__ds.files().create(**http_args).execute()
        fid = response.get('id')
        if isFolder:
            return GFolder(self.__ds, idpath=self.__idPath+[fid])
        else:
            return GFile(self.__ds, fid)

    def Open(self, folderName):
        '''
        Get GFolder object under current folder
        '''
        fid = self.__openFromPidName(self.__idPath[-1], folderName)
        assert fid is not None
        return GFolder(self.__ds, idpath=self.__idPath+[fid])

    def Download(self, filename, LocalPath=None):
        '''
        Download file from google drive
        '''
        LocalPath = LocalPath or filename
        assert False
