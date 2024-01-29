from ..utils.session import Session
from ..response_types import Subdir, FileData
from ..utils.path import Path
from typing import Union, Iterable
from . import File

class Folder:
    def __init__(self, path:str|Path, session:Session):
        if isinstance(path, str):
            path = Path(path)

        self.__ss = session
        self.__path = path
        self.__subdirectories:list[Subdir|Folder] = []
        self.__files:list[File] = []
        self.__is_not_root = bool(str(path))
        try:
            self.__path_name = path.parts[-1]
        except IndexError:
            self.__path_name = ""

        folder_data:list[FileData | Subdir] = session.get("https://dashboard.blomp.com/dashboard/folder?prefix",
                                                          params=dict(prefix=self.__path.as_dir(end_sep=self.__is_not_root))).json()["data"]
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
    
    @property
    def parent(self) -> str:
        return self.__path.parent.as_dir(end_sep=bool(str(self.__path.parent)))
    
    @property
    def path(self) -> str:
        return self.__path.as_dir(end_sep=self.__is_not_root)

    def create_folder(self, name:str):
        self.__ss.post("https://dashboard.blomp.com/dashboard/storage/create_folder",
                       data={"_token": self.__ss.token, "pseudo-folder": self.__path.as_dir(end_sep=self.__is_not_root), "folder_name": name+"/"})
        
    def paste(self, file_or_folder:Union[File, "Folder"], cut:bool=False) -> bool:
        ff = file_or_folder
        is_file = isinstance(ff, File)
        params = dict(
            original_path = ff.file_path if is_file else ff.path,
            action = "move" if cut else "copy",
            target_path = self.__path.as_dir(end_sep=self.__is_not_root),
            file_name = ff.name if is_file else "",
            type = "file" if is_file else "folder"
        )
        response = self.__ss.get("https://dashboard.blomp.com/dashboard/file/move", params=params)
        
        if response.text == "success":
            self.__init__(self.__path, self.__ss)
            return True
        
        return False
    
    def upload(self):
        return NotImplemented