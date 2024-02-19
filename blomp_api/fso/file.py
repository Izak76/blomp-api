from ..response_types import FileData, ShareLinkResponse
from ..utils.monitor import DownloadMonitor, Monitor
from ..utils.path import Path
from ..utils.session import Session

from datetime import datetime
from requests import Response
from threading import Thread
from typing import BinaryIO, Callable, Iterable, Optional, Tuple, Union

import os
import pathlib


class File:
    """Class to manipulate a file stored in the Blomp Cloud"""

    def __init__(self, path: Union[Path, str], dataobj: FileData, session: Session):
        if isinstance(path, str):
            path = Path(path)

        self.__hash: str = dataobj["hash"]
        self.__last_modified: datetime = datetime.fromisoformat(dataobj["last_modified"])
        self.__length: int = dataobj["bytes"]
        self.__name: str = Path(dataobj["name"]).parts[-1]
        self.__content_type: str = dataobj["content_type"]

        self.__ss = session
        self.__path = path
        self.__file_id: Optional[int] = None
        self.__share_status: Optional[bool] = None
        self.__link: Optional[str] = None
        self.__file_path: str = str(self.__path/Path(self.__name))

    def __hash__(self) -> int:
        return hash(self.__hash)

    def __len__(self) -> int:
        return self.__length

    def __repr__(self) -> str:
        return f"File({self.__path}/{self.__name})"

    def __str__(self) -> str:
        return self.__name

    def __downloader(self, _response: Response, _file: BinaryIO, _buffer_size: int, _close: bool, _update_func: Callable[[int], None]):
        for chunk in _response.iter_content(_buffer_size):
            _update_func(_file.write(chunk))
            _file.flush()

        if _close:
            _file.close()

    def _parent_path_changed(self, new_path: Path):
        self.__path = new_path
        self.__file_path: str = str(self.__path/Path(self.__name))

    def __share_info(self):
        info: ShareLinkResponse = self.__ss.get("https://dashboard.blomp.com/dashboard/file/share/link",
                                                params=dict(path=self.__file_path, size=self.__length)).json()["info"]
        info["link"] = f"https://sharedby.blomp.com/{info['link']}"
        self.__file_id = info["id"]
        self.__share_status = bool(info["status"])
        self.__link = info["link"]

    @property
    def content_type(self) -> str:
        """Mime type of file"""

        return self.__content_type

    @property
    def file_path(self) -> str:
        """Full file path"""

        return self.__file_path

    @property
    def last_modified(self) -> datetime:
        """Date and time the file was last modified"""

        return self.__last_modified

    @property
    def md5_hash(self):
        """File MD5 hash"""

        return self.__hash

    @property
    def name(self) -> str:
        """File name"""

        return self.__name

    @property
    def size(self) -> int:
        """File size"""

        return self.__length

    def download(self, file_or_path: Union[str, pathlib.Path, BinaryIO] = "", buffer_size: int = 8192) -> Tuple[Thread, Monitor]:
        """Downloads the file to a specified directory or file-like object.

        Parameters
        ----------
        file_or_path : `str` or `pathlib.Path` or file-like object
            If this parameter is a string or a Path, then it can be a directory or file path.
            If the parameter value exists as a directory, then the file will be saved in this directory with the same name as this file.
            Otherwise (path + file name or just the file name), the parameter will be opened as a file, with its contents being saved there.

            If this parameter is a file-like object, the content will be saved in it.
        buffer_size : int, optional
            Size, in bytes, of the content downloaded in each iteration. (Default: 8192)

        Returns
        -------
        download_thread : `threading.Thread`
            A function thread responsible for downloading the file.
        download_monitor : DownloadMonitor
            An object that can be used to monitor download progress.
        """

        fp = file_or_path
        close = False
        r = self.__ss.get("https://dashboard.blomp.com/dashboard/storage/download_object", stream=True,
                          params=dict(path=self.__file_path, filename=self.__name, size=self.__length))

        if isinstance(fp, (str, pathlib.Path)):
            if isinstance(fp, str):
                fp = pathlib.Path(fp)

            if os.path.isdir(fp):
                fp /= pathlib.Path(self.__name)

            fp = open(fp, 'wb')
            close = True

        monitor = DownloadMonitor(self.__length)
        thread = Thread(target=self.__downloader, args=(
            r, fp, buffer_size, close, monitor._update))
        thread.start()

        return thread, monitor

    def rename(self, new_name: str) -> bool:
        """Rename this file

        Parameters
        ----------
        new_name : `str`
            New name for this file

        Returns
        -------
        success : `bool`
            True, if the server reports that the operation was successful, or False otherwise.
        """

        path_ = self.__path.as_dir(end_sep=bool(self.__path))
        r = self.__ss.get("https://dashboard.blomp.com/dashboard/file/rename",
                          params=dict(original_name=self.__name, type="file", name=new_name, path=path_))

        success = r.text == "success"
        if success:
            self.__name = new_name
            self.__share_info()

        return success

    def share(self, emails: Optional[Iterable[str]] = None, anyone_can_view: bool = False) -> str:
        """Enables the sharing feature for this file.

        Parameters
        ----------
        emails : `Iterable[str]`, optional
            Emails that will receive the shared file link. (Default: None (The link will not be sent to any email))
        anyone_can_view : `bool`, optional
            If True, anyone on the internet can see this file. If False, only added registered users (see email parameter) can see the file (theoretically).

        Returns
        -------
        link : `str`
            Shared file link
        """

        perm = int(bool(anyone_can_view))

        if emails:
            if not all(map(lambda o: isinstance(o, str), emails)):
                raise TypeError("All e-mails must be string")
            emails = str(emails).replace(" ", '')
        else:
            emails = ""

        if self.__file_id is None:
            self.__share_info()

        self.__ss.post("https://dashboard.blomp.com/dashboard/file/share/send",
                       data=dict(_token=self.__ss.token, email=emails,
                                 link=self.__link, permission=perm),
                       allow_redirects=False)

        return self.__link  # type: ignore

    def share_switch_off(self) -> bool:
        """Enables sharing of this file.

        Returns
        -------
        success : `bool`
            True, if the server reports that the operation was successful, or False otherwise.
        """

        if self.__file_id is None:
            self.__share_info()

        if not self.__share_status:
            raise Exception("This file is not being shared")

        r = self.__ss.get("https://dashboard.blomp.com/dashboard/file/share/switch",
                          params=dict(status=0, id=self.__file_id))
        self.__share_status = False

        return r.text == "success"

    def share_switch_on(self) -> bool:
        """Disables sharing of this file.

        Returns
        -------
        success : `bool`
            True, if the server reports that the operation was successful, or False otherwise.
        """

        if self.__file_id is None:
            self.__share_info()

        if self.__share_status:
            raise Exception("This file is already being shared")

        r = self.__ss.get("https://dashboard.blomp.com/dashboard/file/share/switch",
                          params=dict(status=1, id=self.__file_id))
        self.__share_status = True

        return r.text == "success"
