class Monitor:
    def __init__(self, total_size:int):
        self.__total = total_size
        self.__loaded = 0
    
    def _update(self, loaded:int):
        self.__loaded += loaded
    
    @property
    def total(self) -> int:
        return self.__total
    
    @property
    def loaded(self) -> int:
        return self.__loaded
    
    @property
    def progress(self) -> float:
        return self.__loaded/self.__total