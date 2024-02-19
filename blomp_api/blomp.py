from .utils.user_agent import get_user_agent
from .utils.session import Session
from .fso import *

from typing import Optional
import re


class Blomp:
    """
    Class to sign in the Blomp account and access its files and folders. It also provides some information that may be relevant.

    Parameters
    ----------
    email : `str`
        Blomp account e-mail
    password : `str`
        Blomp account password

    Raises
    ------
    ConnectionError
        Raised if e-mail and/or password entered is incorrect, or if connection to server fails.
    """

    def __init__(self, email: str, password: str):
        self.__ss = Session()
        self.__ss.headers["User-Agent"] = get_user_agent()
        self.__ss.headers["Referer"] = "https://www.blomp.com/"
        p = self.__ss.post("https://dashboard.blomp.com/authorize",
                           data={"email": email, "password": password})

        if p.url == "https://dashboard.blomp.com":
            raise ConnectionError("Incorrect email or password")

        if p.status_code >= 400:
            raise ConnectionError(f"Login returned status code {p.status_code}")

        content = next(p.iter_content(8192, True))
        self.__ss.token = re.findall(r'<meta name="csrf_token" content="(.+)" />', content)[0]
        self.__ss.client_id = int(re.findall(r'<input type="hidden" id="clientId" value="(\d+)">', content)[0])

        index_page = self.__ss.get("https://dashboard.blomp.com/dashboard/index").text
        blomp_info = dict(
            used_storage=re.search(r'<h5>Used Storage: (.+)</h5>', index_page),
            avaliable_storage=re.search(r'<h5>Available Storage: (.+)</h5>', index_page),
            storage_capacity=re.search(r'Storage Capacity:\n(.+)</h5>', index_page),
            shared_files=re.search(r'<h5>Shared Files: (.+)</h5>', index_page),
            files_and_folders=re.search(r'<h5>Files & Folders: (.+)</h5>', index_page)
        )

        for attr, match in blomp_info.items():
            if match:
                setattr(self, "__"+attr, match.groups()[0])

    @property
    def available_storage(self) -> Optional[str]:
        """Available storage in Blomp account, or None if this information cannot be obtained."""

        return getattr(self, "__avaliable_storage", None)

    @property
    def files_and_folders(self) -> Optional[int]:
        """Number of stored files and folders, or None if this information cannot be obtained."""

        ff: Optional[str] = getattr(self, "__files_and_folders", None)

        if isinstance(ff, str):
            return int(ff)

        return None

    @property
    def shared_files(self) -> Optional[int]:
        """Number of shared files, or None if this information cannot be obtained."""

        ff: Optional[str] = getattr(self, "__shared_files", None)

        if isinstance(ff, str):
            return int(ff)

        return None

    @property
    def storage_capacity(self) -> Optional[str]:
        """Total storage in the Blomp account, or None if this information cannot be obtained."""

        ff: Optional[str] = getattr(self, "__storage_capacity", None)

        if isinstance(ff, str):
            return ff.strip()

        return None

    @property
    def used_storage(self) -> Optional[str]:
        """Used storage in the Blomp account, or None if this information cannot be obtained."""

        return getattr(self, "__used_storage", None)

    def get_root_directory(self) -> Folder:
        """Returns a Folder object from the root directory"""

        return Folder("", None, self.__ss)
