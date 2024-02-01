from typing import Any
import abc


class Monitor(abc.ABC):
    def __init__(self, total_size:int):
        self._total = total_size
        self._loaded = 0
    
    def __repr__(self) -> str:
        return "{0}(loaded={1}, total={2})".format(self.__class__.__name__, self._loaded, self._total)
    
    @abc.abstractmethod
    def _update(self, loaded:Any):
        self._loaded += loaded
    
    @property
    def total(self) -> int:
        return self._total
    
    @property
    def loaded(self) -> int:
        return self._loaded
    
    @property
    def progress(self) -> float:
        return self._loaded/self._total