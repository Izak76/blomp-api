from requests_toolbelt import MultipartEncoderMonitor
from typing import Union, Iterable
from io import BufferedIOBase
from threading import Thread
from uuid import uuid4

from ..utils.session import Session
from ..utils.monitor import UploadMonitor, Monitor
from ..response_types import Subdir, FileData
from ..utils.path import Path
from . import File

import mimetypes
import pathlib


class Folder:
    def __init__(self, path:str|Path, session:Session):
        if isinstance(path, str):
            path = Path(path)

        self.__ss = session
        self.__path = path
        self.__path_str = self.__path.as_dir(end_sep=bool(str(path)))
        self.__subdirectories:list[Subdir|Folder] = []
        self.__files:list[File] = []
        try:
            self.__path_name = path.parts[-1]
        except IndexError:
            self.__path_name = ""

        folder_data:list[FileData | Subdir] = session.get("https://dashboard.blomp.com/dashboard/folder?prefix",
                                                          params=dict(prefix=self.__path_str)).json()["data"]
        for fd in folder_data:
            if "subdir" in fd:
                self.__subdirectories.append(fd)
                continue

            if fd["content_type"] != "application/directory":
                self.__files.append(File(path, fd, session))
    
    def __getitem__(self, i:int) -> Union[File, "Folder"]:
        if i < len(self.__subdirectories):
            sd = self.__subdirectories[i]

            if isinstance(sd, dict):
                sd = Folder(Path(sd["subdir"]), self.__ss)
                self.__subdirectories[i] = sd

            return sd
        
        return  self.__files[i-len(self.__subdirectories)]
    
    def __iter__(self) -> Iterable[Union[File, "Folder"]]:
        return map(self.__getitem__, range(len(self.__subdirectories)+len(self.__files)))
    
    def __repr__(self) -> str:
        dirs = ", ".join(map(lambda s: str(s) if isinstance(s, Folder) else str(Path(s["subdir"]).parts[-1]), self.__subdirectories))
        files = ", ".join(map(str, self.__files))
        return "Folder(path={0}, subdirectories=[{1}], files=[{2}])".format(str(self.__path), dirs, files)
    
    def __str__(self) -> str:
        return self.__path_name
    
    def __uploader(self, _multi_encoder:MultipartEncoderMonitor):
        self.__ss.post("https://dashboard.blomp.com/dashboard/storage/upload_object",
                       data=_multi_encoder, headers={"Content-Type": _multi_encoder.content_type})
    
    @staticmethod
    def __guess_mime(file_uri:str) -> str:
        mime = mimetypes.guess_type(file_uri)[0]

        return mime if mime else "application/octet-stream"
    
    @property
    def parent(self) -> str:
        return self.__path.parent.as_dir(end_sep=bool(str(self.__path.parent)))
    
    @property
    def path(self) -> str:
        return self.__path_str

    def create_folder(self, name:str):
        self.__ss.post("https://dashboard.blomp.com/dashboard/storage/create_folder",
                       data={"_token": self.__ss.token, "pseudo-folder": self.__path_str, "folder_name": name+"/"})
        
    def paste(self, file_or_folder:Union[File, "Folder"], cut:bool=False) -> bool:
        ff = file_or_folder
        is_file = isinstance(ff, File)
        params = dict(
            original_path = ff.file_path if is_file else ff.path,
            action = "move" if cut else "copy",
            target_path = self.__path_str,
            file_name = ff.name if is_file else "",
            type = "file" if is_file else "folder"
        )
        response = self.__ss.get("https://dashboard.blomp.com/dashboard/file/move", params=params)
        
        if response.text == "success":
            self.__init__(self.__path, self.__ss)
            return True
        
        return False
    
    def upload(self, file:str|pathlib.Path|BufferedIOBase, file_name:str|None=None, file_size:int|None=None) -> tuple[Thread, Monitor]:
        if isinstance(file, (str, pathlib.Path)):
            file = open(file, 'rb')
        
        if not file_name:
            if not hasattr(file, "name"):
                raise ValueError('Unable to determine file name. The "file_name" attribute must be specified')
            
            file_name = pathlib.Path(file.name).parts[-1] # type: ignore
        
        if file_size is None:
            if not file.seekable():
                raise ValueError('Unable to determine file size. The "file_size" attribute must be specified')
            
            s = file.seek(0, 1)
            file_size = file.seek(0, 2)
            file.seek(s)
        
        boundary = str(uuid4())
        monitor = UploadMonitor(file_size)

        me = MultipartEncoderMonitor.from_fields({
            "dzUuid": boundary,
            "dzChunkIndex": "0",
            "dzTotalFileSize": str(file_size),
            "dzCurrentChunkSize": str(file_size),
            "dzTotalChunkCount": "1",
            "dzChunkByteOffset": "0",
            "dzChunkSize": str(file_size+1),
            "dzFilename": file_name,

            "folder": self.__path_str,
            "sub_folder": "",
            "_token": self.__ss.token,
            "client-id": str(self.__ss.client_id),
            "pseudo-folder": self.__path_str,
            "myfile": (file_name, file, self.__guess_mime(file_name)) # type: ignore
        }, boundary, callback=monitor._update)

        thread = Thread(target=self.__uploader, args=[me])
        thread.start()

        return thread, monitor