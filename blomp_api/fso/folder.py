from ..response_types import FileData, Subdir
from ..utils.monitor import Monitor, UploadMonitor
from ..utils.path import Path
from ..utils.session import Session
from . import File

from http.client import HTTPSConnection
from requests_toolbelt import MultipartEncoder
from requests_toolbelt.multipart.encoder import total_len
from threading import Thread
from typing import BinaryIO, Callable, Iterator, List, Optional, Tuple, Union
from urllib.request import Request
from uuid import uuid4

import mimetypes
import pathlib


class Folder:
    """Class to manipulate a folder stored in the Blomp Cloud"""

    def __init__(self, path: Union[str, Path], parent: Optional["Folder"], session: Session):
        if isinstance(path, str):
            path = Path(path)

        self.__ss = session
        self.__subdirectories: List[Union[Subdir, Folder]] = []
        self.__files: List[File] = []
        self.__parent = parent
        self.__path = path
        self._self_path_changed(bool(path))
        self.reload()

    def __getitem__(self, i: int) -> Union[File, "Folder"]:
        if i < len(self.__subdirectories):
            sd = self.__subdirectories[i]

            if isinstance(sd, dict):
                sd = Folder(Path(sd["subdir"]), self, self.__ss)
                self.__subdirectories[i] = sd

            return sd

        return self.__files[i-len(self.__subdirectories)]

    def __iter__(self) -> Iterator[Union[File, "Folder"]]:
        return map(self.__getitem__, range(len(self.__subdirectories)+len(self.__files)))

    def __repr__(self) -> str:
        dirs = ", ".join(map(
            lambda s: str(s) if isinstance(s, Folder) else str(Path(s["subdir"]).parts[-1]),
            self.__subdirectories))
        files = ", ".join(map(str, self.__files))

        return f"Folder(path={str(self.__path)}, subdirectories=[{dirs}], files=[{files}])"

    def __str__(self) -> str:
        return self.__path_name

    def __uploader(self, _multi_encoder: MultipartEncoder, _file_size: int, _buffer_size: int, _update_func: Callable[[int], None]):
        url, path = "https://dashboard.blomp.com", "/dashboard/storage/upload_object"
        conn: HTTPSConnection = self.__ss.adapters['https://'].get_connection(url)._get_conn()
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

    def _parent_path_changed(self, new_path: Path):
        self.__path = new_path/self.__path_name
        self._self_path_changed()

    def _self_path_changed(self, not_is_root: bool = True):
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
    def __guess_mime(file_uri: str) -> str:
        mime = mimetypes.guess_type(file_uri)[0]

        return mime if mime else "application/octet-stream"

    @property
    def files(self) -> Tuple[File, ...]:
        """Tuple with all files in this folder"""

        return tuple(self.__files)

    @property
    def name(self):
        """Name of this folder"""

        return self.__path_name

    @property
    def parent(self) -> Optional["Folder"]:
        """Parent folder of this folder, if it exists (if this folder is root, None is returned)"""

        return self.__parent

    @property
    def path(self) -> str:
        """Path of this folder"""

        return self.__path_str

    @property
    def subfolders(self) -> Tuple["Folder", ...]:
        """Tuple with all subfolders in this folder"""

        return tuple(map(self.__getitem__, range(len(self.__subdirectories)))) # type: ignore

    def create_folder(self, name: str):
        """Create a new folder in this directory.

        Parameters
        ----------
        name : `str`
            Name of the folder to be created.
        """

        self.__ss.post("https://dashboard.blomp.com/dashboard/storage/create_folder",
                       data={"_token": self.__ss.token, "pseudo-folder": self.__path_str, "folder_name": name+"/"})

    def delete(self, item: Union[File, "Folder", str]) -> bool:
        """Deletes a folder or file in this directory.

        Parameters
        ----------
        item : File or Folder or `str`
            If this parameter is a File or Folder object, it must belong to this folder.
            If this parameter is a string, it must be the name of a folder or file belonging to this folder.

        Returns
        -------
        success : `bool`
            True, if the server reports that the operation was successful, or False otherwise.

        Raises
        ------
        FileNotFoundError
            Raised if `item` parameter is not found in this folder.
        """

        if isinstance(item, str):
            item_ = (self.get_file_by_name(item) or
                     self.get_folder_by_name(item))
            if item_ is None:
                raise FileNotFoundError("Item not found")

            item = item_

        if isinstance(item, File):
            r = self.__ss.get("https://dashboard.blomp.com/dashboard/storage/delete_object",
                              params=dict(path=item.file_path))

        else:
            r = self.__ss.get("https://dashboard.blomp.com/dashboard/storage/delete_folder",
                              params=dict(folder=item.__path_str))

        return bool(r.json()["response"])

    def get_file_by_name(self, name: str) -> Optional[File]:
        """Finds a file in this folder by name and returns it, if exists.

        Parameters
        ----------
        name : `str`
            File name to find

        Returns
        -------
        file : File or None
            If the file is found, then a `File` object of it will be returned.
            Otherwise, None will be returned.
        """

        for file in self.__files:
            if file.name == name:
                return file

    def get_folder_by_name(self, name: str) -> Optional["Folder"]:
        """Finds a subfolder in this folder by name and returns it, if exists.

        Parameters
        ----------
        name : `str`
            Folder name to find

        Returns
        -------
        folder : Folder or None
            If the folder is found, then a `Folder` object of it will be returned.
            Otherwise, None will be returned.
        """

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

    def paste(self, file_or_folder: Union[File, "Folder"], cut: bool = False) -> bool:
        """Pastes a file or folder from another directory into this folder

        Parameters
        ----------
        file_or_folder : File or Folder
            `File` or `Folder` object from another directory to be pasted into this folder.
        cut : bool, optional
            If `True`, the file/folder will be cut from its old directory and pasted into this folder.
            If `False`, the file/folder will be copied to this folder. (Default: False)

        Returns
        -------
        success : bool
            True, if the server reports that the operation was successful, or False otherwise.
        """

        ff = file_or_folder
        is_file = isinstance(ff, File)
        params = dict(
            original_path=ff.file_path if is_file else ff.path,
            action="move" if cut else "copy",
            target_path=self.__path_str,
            file_name=ff.name if is_file else "",
            type="file" if is_file else "folder"
        )
        response = self.__ss.get("https://dashboard.blomp.com/dashboard/file/move", params=params)

        if response.text == "success":
            ff._parent_path_changed(self.__path)
            return True

        return False

    def reload(self):
        """This method updates the data in this folder. It should only be called when there are changes to this folder."""

        folder_data: List[Union[FileData, Subdir]] = self.__ss.get("https://dashboard.blomp.com/dashboard/folder?prefix",
                                                             params=dict(prefix=self.__path_str)).json()["data"]
        subdirectories: List[Subdir] = []
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

    def rename(self, new_name: str) -> bool:
        """Renames this folder. This method **is unsafe**. Use the `safe_rename` method instead.

        Parameters
        ----------
        new_name : `str`
            New name for this folder.

        Returns
        -------
        success : `bool`
            True, if the server reports that the operation was successful, or False otherwise.

        Warnings
        --------
        RuntimeWarning
            Raised when calling this method due to its unsafe, as it tries to directly rename the folder.
            Directly renaming a folder in the Blomp Cloud may not work correctly as there is a bug where the renaming process may end incompletely.
            To rename this folder, use the `safe_rename` method instead.
        """

        if not bool(self.__path):
            raise PermissionError("Unable to rename root folder")

        from warnings import warn
        warn('This method may not work correctly. It is recommended to use the "safe_rename" method instead.', RuntimeWarning)

        r = self.__ss.get("https://dashboard.blomp.com/dashboard/file/rename",
                          params=dict(original_name=self.__path_name, type="folder", name=new_name, path=self.__path_str))

        success = r.text == "success"
        if success:
            self.__path = self.__path.parent/new_name
            self._self_path_changed()

        return success

    def safe_rename(self, new_name: str):
        """Renames this folder. Use this method instead of `rename` method.

        Parameters
        ----------
        new_name : `str`
            New name for this folder.

        Notes
        -----
        This method creates a new folder with the name specified in the `new_name` parameter in the parent directory of this folder.
        After that, all files and folders in this directory are cut and pasted into the new folder, and then this now empty folder is deleted.
        This process may take a while, depending on the number of files present in this folder, but it is much safer than the `rename` method, which renames the folder directly.
        Apparently, when directly renaming a folder, the Blomp Cloud does the same process described here, but incompletely in some cases, which makes the `rename` method unsafe.
        """

        if self.__parent is None:
            raise PermissionError("Unable to rename root folder")

        self.__parent.create_folder(new_name)
        new_folder: Folder = self.__parent.get_folder_by_name(new_name)  # type: ignore

        for ff in self:
            new_folder.paste(ff, True)

        self.__parent.delete(self)
        self.__path = new_folder.__path
        self._self_path_changed()

    def upload(self, file: Union[str, pathlib.Path, BinaryIO], file_name: Optional[str] = None, replace_if_exists: bool = False, buffer_size: int = 8192) -> Tuple[Thread, Monitor]:
        """Upload a file to this folder

        Parameters
        ----------
        file : `str` or `pathlib.Path` or file-like object
            If this parameter is a string or a Path, then this must be a path to an existing file.
            If this parameter is a file-like object, then its contents will be uploaded.
        file_name : `str`, optional
            If specified, then the file will have the name specified in this parameter in the Blomp Cloud.
            Otherwise (`file_name=None`), the file name will be obtained automatically if possible.
            (Default: None)
        file_size : int, optional
            File size in bytes. If not specified, the file size will be obtained automatically if possible.
            (Default: None (obtained automatically))
        replace_if_exists : bool, optional
            Parameter considered only when a file with the same name already exists in this folder.
            If True, the existing file is replaced by the new one to be uploaded.
            If False, `FileExistsError` is raised. (Default: False)
        buffer_size : int, optional
            Size, in bytes, of the content uploaded in each iteration. (Default: 8192)

        Returns
        -------
        upload_thread : `threading.Thread`
            A function thread responsible for uploading the file.
        upload_monitor : UploadMonitor
            An object that can be used to monitor upload progress.

        Raises
        ------
        ValueError
            Raised when the file name or size cannot be automatically determined if the `file_name` parameter are not specified.
        FileExistsError
            Raised when a file with the same name already exists in this directory, and the `replace_if_exists` parameter is False.
        """

        if isinstance(file, (str, pathlib.Path)):
            file = open(file, 'rb')

        if not file_name:
            if not hasattr(file, "name"):
                raise ValueError('Unable to determine file name. The "file_name" parameter must be specified')

            file_name = pathlib.Path(file.name).parts[-1]  # type: ignore

        file_size = total_len(file)

        if not file_size and file.seekable():
            s = file.seek(0, 1)
            file_size = file.seek(0, 2)
            file.seek(s)
        
        else:
            raise ValueError('Unable to determine file size')

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
            "myfile": (file_name, file, self.__guess_mime(file_name))
        }, boundary)

        thread = Thread(target=self.__uploader, args=[
                        me, file_size, buffer_size, monitor._update])
        thread.start()

        return thread, monitor
