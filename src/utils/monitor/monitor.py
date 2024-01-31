from typing import Any
import abc


class Monitor(abc.ABC):
    def __init__(self, total_size:int):
        self.__total = total_size
        self.__loaded = 0
    
    @abc.abstractmethod
    def _update(self, loaded:Any):
        pass
    
    @property
    def total(self) -> int:
        return self.__total
    
    @property
    def loaded(self) -> int:
        return self.__loaded
    
    @property
    def progress(self) -> float:
        return self.__loaded/self.__total