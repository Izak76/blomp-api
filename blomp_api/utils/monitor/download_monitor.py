from .monitor import Monitor


class DownloadMonitor(Monitor):
    """Class to monitor download progress"""

    def _update(self, loaded: int):
        super()._update(loaded)
