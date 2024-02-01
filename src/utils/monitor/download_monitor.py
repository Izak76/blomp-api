from .monitor import Monitor


class DownloadMonitor(Monitor):
    def _update(self, loaded:int):
        super()._update(loaded)