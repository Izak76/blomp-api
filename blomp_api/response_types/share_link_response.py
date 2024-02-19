from typing import Optional, TypedDict


class ShareLinkResponse(TypedDict):
    id: int
    container: str
    path: str
    link: str
    added: Optional[str]
    created_at: str
    permission: int
    status: int
    size: int
