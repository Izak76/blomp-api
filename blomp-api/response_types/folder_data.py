from typing import TypedDict


class Subdir(TypedDict):
    subdir: str


class FileData(TypedDict):
    hash:str
    last_modified:str
    bytes:int
    name:str
    content_type:str