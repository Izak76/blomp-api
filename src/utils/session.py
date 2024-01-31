from requests import Session as SS


class Session(SS):
    def __init__(self):
        super().__init__()
        self.__token:str = ""
        self.__client_id:int = 0
    
    @property
    def client_id(self):
        return self.__client_id
    
    @client_id.setter
    def client_id(self, id_:int):
        self.__client_id = id_

    @property
    def token(self) -> str:
        return self.__token
    
    @token.setter
    def token(self, tok:str):
        self.__token = tok


__all__ = ["Session"]