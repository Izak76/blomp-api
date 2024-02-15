from .monitor import Monitor


class UploadMonitor(Monitor):
    """Class to monitor upload progress"""

    def _update(self, loaded: int):
        super()._update(loaded)
