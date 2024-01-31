from datetime import datetime
from requests import Response
from threading import Thread
from io import BufferedIOBase
from typing import Iterable, Callable

from ..utils.path import Path
from ..utils.session import Session
from ..utils.monitor import DownloadMonitor, Monitor
from ..response_types import ShareLinkResponse, FileData

import os, pathlib


class File:
    def __init__(self, path:str|Path, dataobj:FileData, session:Session):
        if isinstance(path, str):
            path = Path(path)

        self.__hash:str = dataobj["hash"]
        self.__last_modified:datetime = datetime.fromisoformat(dataobj["last_modified"])
        self.__length:int = dataobj["bytes"]
        self.__name:str = Path(dataobj["name"]).parts[-1]
        self.__content_type:str = dataobj["content_type"]

        self.__ss = session
        self.__path = path
        self.__file_id:int|None = None
        self.__share_status:bool|None = None
        self.__link:str|None = None
        self.__file_path:str = str(self.__path/Path(self.__name))
    
    def __hash__(self) -> int:
        return hash(self.__hash)
    
    def __len__(self) -> int:
        return self.__length
    
    def __repr__(self) -> str:
        return "File({0}/{1})".format(self.__path, self.__name)
    
    def __str__(self) -> str:
        return self.__name
    
    def __downloader(self, _response:Response, _file:BufferedIOBase, _buffer_size:int, _update_func:Callable[[int], None]):
        with _file:
            for chunk in _response.iter_content(_buffer_size):
                _update_func(_file.write(chunk))
                _file.flush()

    @property
    def content_type(self) -> str:
        return self.__content_type
    
    @property
    def file_path(self) -> str:
        return self.__file_path
    
    @property
    def last_modified(self) -> datetime:
        return self.__last_modified
    
    @property
    def md5_hash(self):
        return self.__hash
    
    @property
    def name(self) -> str:
        return self.__name
    
    @property
    def size(self) -> int:
        return self.__length
    
    def delete(self) -> bool:
        r = self.__ss.get("https://dashboard.blomp.com/dashboard/storage/delete_object", params=dict(path=self.__file_path))

        return bool(r.json()["response"])
    
    def download(self, file_or_path:str|pathlib.Path|BufferedIOBase=".", buffer_size:int=4096) -> tuple[Thread, Monitor]:
        fp = file_or_path
        r = self.__ss.get("https://dashboard.blomp.com/dashboard/storage/download_object", stream=True,
                          params=dict(path=self.__file_path, filename=self.__name, size=self.__length))
        
        if isinstance(fp, (str, pathlib.Path)):
            if isinstance(fp, str):
                fp = pathlib.Path(fp)

            if os.path.isdir(fp):
                fp /= pathlib.Path(self.__name)
            
            fp = open(fp, 'wb')
        
        monitor = DownloadMonitor(self.__length)
        thread = Thread(target=self.__downloader, args=(r, fp, buffer_size, monitor._update))
        thread.start()

        return thread, monitor

    def rename(self, new_name:str) -> bool:
        path_ = str(self.__path)
        r = self.__ss.get("https://dashboard.blomp.com/dashboard/file/rename",
                          params=dict(original_name=self.__name, type="file", name=new_name, path=path_))
        
        success =  r.text == "success"
        if success:
            self.__name = new_name
            self.share_info()
        
        return success
    
    def share(self, emails:Iterable[str]|None=None, anyone_can_view:bool=False) -> str:
        perm = int(bool(anyone_can_view))

        if emails:
            if not all(map(lambda o: isinstance(o, str), emails)):
                raise TypeError("All e-mails must be string")
            emails = str(emails).replace(" ", '')
        else:
            emails = ""

        if self.__file_id is None:
            self.share_info()

        self.__ss.post("https://dashboard.blomp.com/dashboard/file/share/send", 
                       data=dict(_token=self.__ss.token, email=emails, link=self.__link, permission=perm),
                       allow_redirects=False)
        
        return self.__link # type: ignore
    
    def share_info(self) -> ShareLinkResponse:
        # TODO: Tornar esse método "privado"
        info: ShareLinkResponse = self.__ss.get("https://dashboard.blomp.com/dashboard/file/share/link",
                            params=dict(path=self.__file_path, size=self.__length)).json()["info"]
        info["link"] = "https://sharedby.blomp.com/"+info["link"]
        self.__file_id = info["id"]
        self.__share_status = bool(info["status"])
        self.__link = info["link"]

        return info
    
    def share_switch_off(self) -> bool:
        if self.__file_id is None:
            self.share_info()
        
        if not self.__share_status:
            raise Exception("This file is not being shared")
        
        r = self.__ss.get("https://dashboard.blomp.com/dashboard/file/share/switch", params=dict(status=0, id=self.__file_id))
        self.__share_status = False

        return r.text == "success"
    
    def share_switch_on(self) -> bool:
        if self.__file_id is None:
            self.share_info()

        if self.__share_status:
            raise Exception("This file is already being shared")
        
        r = self.__ss.get("https://dashboard.blomp.com/dashboard/file/share/switch", params=dict(status=1, id=self.__file_id))
        self.__share_status = True
        
        return r.text == "success"
    
