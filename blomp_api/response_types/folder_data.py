from typing import TypedDict


class FileData(TypedDict):
    hash: str
    last_modified: str
    bytes: int
    name: str
    content_type: str


class Subdir(TypedDict):
    subdir: str