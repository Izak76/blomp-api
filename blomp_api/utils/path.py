import re


class Path:
    """Class to represent a path of a file or folder

    Parameters
    ----------
    initial_path : `str`
        Path to be represented by this class.
    path_char : `str`, optional
        Character to be used as separator of path components. (Default: '/')
    """

    def __init__(self, initial_path: str = "", path_char: str = "/"):
        self.__path_char = path_char
        self.__path_parts = tuple(filter(None, re.split(r"/|\\", initial_path)))
        self.__path_str = path_char.join(self.__path_parts)

    def __bool__(self) -> bool:
        return bool(self.__path_parts)

    def __repr__(self) -> str:
        return f"Path({self.__path_str})"

    def __str__(self) -> str:
        return self.__path_str

    def __truediv__(self, path_: "Path|str") -> "Path":
        if isinstance(path_, str):
            path_ = Path(path_)

        return Path(self.__path_char.join(self.__path_parts+path_.__path_parts))

    def __rtruediv__(self, path_: "Path|str") -> "Path":
        if isinstance(path_, str):
            path_ = Path(path_)

        return path_/self

    @property
    def parts(self) -> tuple[str, ...]:
        """A tuple of strings with path components"""

        return self.__path_parts

    @property
    def parent(self) -> "Path":
        """Parent path of this path"""

        return Path(self.__path_char.join(self.__path_parts[:-1]))

    def as_dir(self, start_sep: bool = False, end_sep: bool = True) -> str:
        """Representation of this path as a directory, with the separator character being added to the beginning and/or end of the path.

        Parameters
        ----------
        start_sep : `bool`
            If True, the separator character will be added at the beginning of path. (Default: False)
        end_sep : `bool`
            If True, the separator character will be added at the end of path. (Default: True)

        Returns
        -------
        path_str : `str`
            Representation of the path as a string, with the separator character being added or not to the beginning and/or end, depending on the parameter values.

        Notas
        -----
        The path separator character is the same as that provided by the `path_char` parameter during the initialization of this class. (Default: '/')
        """

        s = self.__path_char if start_sep else ""
        e = self.__path_char if end_sep else ""

        return s+self.__path_str+e
