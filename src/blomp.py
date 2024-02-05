from .utils.session import Session
from .fso import *
import re


UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
AppleWebKit/537.36 (KHTML, like Gecko) \
Chrome/117.0.0.0 Safari/537.36 \
Edg/117.0.2045.36"

class Blomp:
    def __init__(self, email:str, password:str):
        self.__ss = Session()
        self.__ss.headers["User-Agent"] = UA
        self.__ss.headers["Referer"] = "https://www.blomp.com/"
        p = self.__ss.post("https://dashboard.blomp.com/authorize", data={"email": email, "password": password}, stream=False)

        if p.status_code >= 400:
            raise ConnectionRefusedError("Login returned status code {}".format(p.status_code))
        
        content = next(p.iter_content(8192, True))
        self.__ss.token = re.findall(r'<meta name="csrf_token" content="(.+)" />', content)[0]
        self.__ss.client_id = int(re.findall(r'<input type="hidden" id="clientId" value="(\d+)">', content)[0])

        index_page = self.__ss.get("https://dashboard.blomp.com/dashboard/index").text
        blomp_info = dict(
            used_storage = re.search(r'<h5>Used Storage: (.+)</h5>', index_page),
            avaliable_storage = re.search(r'<h5>Available Storage: (.+)</h5>', index_page),
            storage_capacity = re.search(r'Storage Capacity:\n(.+)</h5>', index_page),
            shared_files = re.search(r'<h5>Shared Files: (.+)</h5>', index_page),
            files_and_folders = re.search(r'<h5>Files & Folders: (.+)</h5>', index_page)
        )

        for attr, match in blomp_info.items():
            if match:
                setattr(self, "__"+attr, match.groups()[0])
    
    @property
    def avaliable_storage(self) -> str|None:
        return getattr(self, "__avaliable_storage", None)
    
    @property
    def files_and_folders(self) -> int|None:
        ff:str|None = getattr(self, "__files_and_folders", None)

        if isinstance(ff, str):
            return int(ff)
        
        return None
    
    @property
    def shared_files(self) -> int|None:
        ff:str|None = getattr(self, "__shared_files", None)

        if isinstance(ff, str):
            return int(ff)
        
        return None
    
    @property
    def storage_capacity(self) -> str|None:
        ff:str|None = getattr(self, "__storage_capacity", None)

        if isinstance(ff, str):
            return ff.strip()
        
        return None
    
    @property
    def used_storage(self) -> str|None:
        return getattr(self, "__used_storage", None)
    
    def get_root_directory(self) -> Folder:
        return Folder("", None, self.__ss)