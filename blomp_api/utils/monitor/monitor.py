from typing import Any
import abc


class Monitor(abc.ABC):
    def __init__(self, total_size: int):
        self._total = total_size
        self._loaded = 0

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(loaded={self._loaded}, total={self._total})"

    @abc.abstractmethod
    def _update(self, loaded: Any):
        self._loaded += loaded

    @property
    def total(self) -> int:
        """Total file size to be loaded"""

        return self._total

    @property
    def loaded(self) -> int:
        """Loaded file size"""

        return self._loaded

    @property
    def progress(self) -> float:
        """File loaded progress, between [0, 1] (basically, loaded_size/total_size)"""

        return self._loaded/self._total
