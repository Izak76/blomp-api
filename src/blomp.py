from .utils.session import Session
from .fso import *
import re


UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
AppleWebKit/537.36 (KHTML, like Gecko) \
Chrome/117.0.0.0 Safari/537.36 \
Edg/117.0.2045.36"

class Blomp:
    def __init__(self, email:str, password:str): # OK
        self.__ss = Session()
        self.__ss.headers["User-Agent"] = UA
        self.__ss.headers["Referer"] = "https://www.blomp.com/"
        p = self.__ss.post("https://dashboard.blomp.com/authorize", data={"email": email, "password": password}, stream=False)

        if p.status_code >= 400:
            raise ConnectionRefusedError("Login returned status code {}".format(p.status_code))
        
        self.__ss.token = re.findall('<meta name="csrf_token" content="(.+)" />', next(p.iter_content(512, True)))[0]
    
    def get_root_directory(self) -> Folder: # OK
        return Folder("", self.__ss)
