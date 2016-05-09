import os
from apiclient.http import MediaFileUpload

class GFile:
    '''
    File on google drive
    '''
    def __init__(self, driveService, file_id, name, modifiedTime):
        '''
        :Args:
            - modifiedTime: e.g. u'2016-05-07T17:27:57.983Z'
        '''
        self.__ds = driveService
        self.__id = file_id
        self.name = name
        self.modifiedTime = modifiedTime


class GFolder:
    '''
    Folder on google drive
    '''
    def __init__(self, driveService, fullpath=None, idpath=None, name=None, modifiedTime=None):
        '''
        Specified one of fullpath or idpath of drive folder, but not both.

        :Args:
            - drive
            - fullpath: a list of folder name start from root,
                        empty list refer to root
            - modifiedTime: e.g. u'2016-05-07T17:27:57.983Z'
        '''
        assert (fullpath is None) != (idpath is None), "Specified either fullpath or idpath"
        self.name = name
        self.modifiedTime = modifiedTime
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
            - (GFolders, GFiles)
        '''
        # list folders
        response = self.__ds.files().list(
            q="'%s' in parents"%(self.__idPath[-1]),
            fields="files(id, modifiedTime, mimeType, name)"
        ).execute()
        gfolders, gfiles = [], []
        for f in response.get('files'):
            if f.get('mimeType') == 'application/vnd.google-apps.folder':
                gfolders += [GFolder(
                    self.__ds,
                    idpath=self.__idPath+[f.get('id')],
                    name=f.get('name'),
                    modifiedTime=f.get('modifiedTime')
                )]
            else:
                gfiles += [GFile(self.__ds, f.get('id'), f.get('name'), f.get('modifiedTime'))]
        return (gfolders, gfiles)

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

    def OpenFiles(self, filename):
        '''
        :Returns:
            - a list of file under self folder with filename
        '''
        response = self.__ds.files().list(
            q="'%s' in parents and name = '%s' and mimeType!='application/vnd.google-apps.folder'"%(self.__idPath[-1], filename),
            fields="files(id, modifiedTime)"
        ).execute()
        fs = response.get('files')
        return [GFile(self.__ds, f.get('id'), filename, f.get('modifiedTime')) for f in fs]

