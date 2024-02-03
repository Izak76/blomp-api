from requests_toolbelt import MultipartEncoder
from http.client import HTTPSConnection
from typing import Union, Callable, Iterator
from urllib.request import Request
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
    def __init__(self, path:str|Path, parent:Union["Folder", None], session:Session):
        if isinstance(path, str):
            path = Path(path)

        self.__ss = session
        self.__subdirectories:list[Subdir|Folder] = []
        self.__files:list[File] = []
        self.__parent = parent
        self.__path = path
        self._self_path_changed(bool(path))
        self.reload()
    
    def __getitem__(self, i:int) -> Union[File, "Folder"]:
        if i < len(self.__subdirectories):
            sd = self.__subdirectories[i]

            if isinstance(sd, dict):
                sd = Folder(Path(sd["subdir"]), self, self.__ss)
                self.__subdirectories[i] = sd

            return sd
        
        return  self.__files[i-len(self.__subdirectories)]
    
    def __iter__(self) -> Iterator[Union[File, "Folder"]]:
        return map(self.__getitem__, range(len(self.__subdirectories)+len(self.__files)))
    
    def __repr__(self) -> str:
        dirs = ", ".join(map(lambda s: str(s) if isinstance(s, Folder) else str(Path(s["subdir"]).parts[-1]), self.__subdirectories))
        files = ", ".join(map(str, self.__files))
        return "Folder(path={0}, subdirectories=[{1}], files=[{2}])".format(str(self.__path), dirs, files)
    
    def __str__(self) -> str:
        return self.__path_name
    
    def __uploader(self, _multi_encoder:MultipartEncoder, _file_size:int, _buffer_size:int, _update_func:Callable[[int], None]):
        url, path = "https://dashboard.blomp.com", "/dashboard/storage/upload_object"
        conn:HTTPSConnection = self.__ss.adapters['https://'].get_connection(url)._get_conn()
        conn.putrequest("POST", path)
        
        for header in self.__ss.headers.items():
            conn.putheader(*header)
        
        conn.putheader("Content-Type", _multi_encoder.content_type)
        conn.putheader("Content-Length", str(_multi_encoder.len))
        conn.putheader("Cookie", "; ".join(map(lambda ck: "=".join(ck), self.__ss.cookies.get_dict().items())))
        conn.endheaders()

        conn.send(_multi_encoder.read(_multi_encoder.len - _file_size))
        data = _multi_encoder.read(_buffer_size)
        while data:
            _update_func(len(data))
            conn.send(data)
            data = _multi_encoder.read(_buffer_size)
        
        response = conn.getresponse()
        if response.getheader("Set-Cookie"):
            self.__ss.cookies.extract_cookies(response, Request(url+path))
        
        self.reload()
    
    def _parent_path_changed(self, new_path:Path):
        self.__path = new_path/self.__path_name
        self._self_path_changed()
    
    def _self_path_changed(self, not_is_root:bool=True):
        self.__path_str = self.__path.as_dir(end_sep=not_is_root)

        try:
            self.__path_name = self.__path.parts[-1]
        except IndexError:
            self.__path_name = ""

        for sd in self.__subdirectories:
            if isinstance(sd, Folder):
              sd._parent_path_changed(self.__path)
        
        for file in self.__files:
            file._parent_path_changed(self.__path)

    @staticmethod
    def __guess_mime(file_uri:str) -> str:
        mime = mimetypes.guess_type(file_uri)[0]

        return mime if mime else "application/octet-stream"
    
    @property
    def files(self) -> tuple[File, ...]:
        return tuple(self.__files)
    
    @property
    def name(self):
        return self.__path_name
    
    @property
    def parent(self) -> Union["Folder", None]:
        return self.__parent
    
    @property
    def path(self) -> str:
        return self.__path_str
    
    @property
    def subfolders(self) -> tuple["Folder", ...]:
        return tuple(map(self.__getitem__, range(len(self.__subdirectories)))) # type: ignore
    
    def create_folder(self, name:str):
        self.__ss.post("https://dashboard.blomp.com/dashboard/storage/create_folder",
                       data={"_token": self.__ss.token, "pseudo-folder": self.__path_str, "folder_name": name+"/"})
    
    def delete(self, item:Union[File, "Folder", str]) -> bool:
        if isinstance(item, str):
            item_ = self.get_file_by_name(item) or self.get_folder_by_name(item)
            if item_ is None:
                raise ValueError("Item not found")
            
            item = item_
        
        if isinstance(item, File):
            r = self.__ss.get("https://dashboard.blomp.com/dashboard/storage/delete_object", params=dict(path=item.file_path))

        else:
            r = self.__ss.get("https://dashboard.blomp.com/dashboard/storage/delete_folder", params=dict(folder=item.__path_str))
        
        return bool(r.json()["response"])

    def get_file_by_name(self, name:str) -> File | None:
        for file in self.__files:
            if file.name == name:
                return file
    
    def get_folder_by_name(self, name:str) -> Union["Folder", None]:
        for i in range(len(self.__subdirectories)):
            folder = self.__subdirectories[i]

            if isinstance(folder, dict):
                p = Path(folder["subdir"])
                if p.parts[-1] == name:
                    folder = Folder(p, self, self.__ss)
                    self.__subdirectories[i] = folder
                    return folder
            
            else:
                if folder.__path_name == name:
                    return folder
                
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
            ff._parent_path_changed(self.__path)
            return True
        
        return False
    
    def reload(self):
        folder_data:list[FileData | Subdir] = self.__ss.get("https://dashboard.blomp.com/dashboard/folder?prefix",
                                                          params=dict(prefix=self.__path_str)).json()["data"]
        subdirectories:list[Subdir] = []
        self.__files.clear()

        for fd in folder_data:
            if "subdir" in fd:
                subdirectories.append(fd)
                continue

            if fd["content_type"] != "application/directory":
                self.__files.append(File(self.__path, fd, self.__ss))
        
        for file in self.__files:
            if file.size >= 104857600:
                for sd in subdirectories:
                    sd_name = Path(sd["subdir"]).parts[-1]
                    if file.name == sd_name:
                        subdirectories.remove(sd)
        
        self.__subdirectories.clear()
        self.__subdirectories.extend(subdirectories)

    def rename(self, new_name:str) -> bool:
        if not bool(self.__path):
            raise PermissionError("Unable to rename root folder")
        
        from warnings import warn
        warn('This method may not work correctly. It is recommended to use the "safe_rename" method', RuntimeWarning)
        
        r = self.__ss.get("https://dashboard.blomp.com/dashboard/file/rename",
                          params=dict(original_name=self.__path_name, type="folder", name=new_name, path=self.__path_str))
        
        success =  r.text == "success"
        if success:
            self.__path = self.__path.parent/new_name
            self._self_path_changed()
        
        return success
    
    def safe_rename(self, new_name:str):
        if self.__parent is None:
            raise PermissionError("Unable to rename root folder")
        
        self.__parent.create_folder(new_name)
        new_folder:Folder = self.__parent.get_folder_by_name(new_name) # type: ignore

        for ff in self:
            new_folder.paste(ff, True)
        
        self.__parent.delete(self)
        self.__path = new_folder.__path
        self._self_path_changed()

    def upload(self, file:str|pathlib.Path|BufferedIOBase, file_name:str|None=None, file_size:int|None=None, replace_if_exists:bool=False, buffer_size:int=8192) -> tuple[Thread, Monitor]:
        if isinstance(file, (str, pathlib.Path)):
            file = open(file, 'rb')
        
        if not file_name:
            if not hasattr(file, "name"):
                raise ValueError('Unable to determine file name. The "file_name" parameter must be specified')
            
            file_name = pathlib.Path(file.name).parts[-1] # type: ignore
        
        if file_size is None:
            if not file.seekable():
                raise ValueError('Unable to determine file size. The "file_size" parameter must be specified')
            
            s = file.seek(0, 1)
            file_size = file.seek(0, 2)
            file.seek(s)
        
        if not replace_if_exists:
            for f in self.__files:
                if f.name == file_name:
                    raise FileExistsError('A file with same was found. Set the "replace_if_exists" parameter to True to replace the old file or set "file_name" parameter')
        
        boundary = str(uuid4())
        monitor = UploadMonitor(file_size)

        me = MultipartEncoder({
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
        }, boundary)

        thread = Thread(target=self.__uploader, args=[me, file_size, buffer_size, monitor._update])
        thread.start()

        return thread, monitor