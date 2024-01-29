import re


class Path:
    def __init__(self, initial_path:str="", path_char="/"):
        self.__path_char = path_char
        self.__path_parts = tuple(filter(None, re.split(r"/|\\", initial_path)))
        self.__path_str = path_char.join(self.__path_parts)
    
    def __repr__(self) -> str:
        return "Path({0})".format(self.__path_str)
    
    def __str__(self) -> str:
        return self.__path_str
    
    def __truediv__(self, path_:"Path|str") -> "Path":
        if isinstance(path_, str):
            path_ = Path(path_)
        
        return Path(self.__path_char.join(self.__path_parts+path_.__path_parts))
    
    def __rtruediv__(self, path_:"Path|str") -> "Path":
        if isinstance(path_, str):
            path_ = Path(path_)
        
        return path_/self
    
    @property
    def parts(self) -> tuple[str, ...]:
        return self.__path_parts
    
    @property
    def parent(self) -> "Path":
        return Path(self.__path_char.join(self.__path_parts[:-1]))
    
    def as_dir(self, start_sep:bool=False, end_sep:bool=True) -> str:
        s = self.__path_char if start_sep else ""
        e = self.__path_char if end_sep else ""

        return s+self.__path_str+e