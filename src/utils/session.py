from requests import Session as SS


class Session(SS):
    def __init__(self):
        super().__init__()
        self.__token = ""
    
    @property
    def token(self) -> str:
        return self.__token
    
    @token.setter
    def token(self, tok:str):
        self.__token = tok


__all__ = ["Session"]