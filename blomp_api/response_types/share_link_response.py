from typing import TypedDict


class ShareLinkResponse(TypedDict):
    id: int
    container: str
    path: str
    link: str
    added: str | None
    created_at: str
    permission: int
    status: int
    size: int
