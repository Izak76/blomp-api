from .monitor import Monitor


class DownloadMonitor(Monitor):
    def _update(self, loaded:int):
        self.__loaded += loaded