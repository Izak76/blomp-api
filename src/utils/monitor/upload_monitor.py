from .monitor import Monitor


class UploadMonitor(Monitor):
    def _update(self, loaded: int):
        super()._update(loaded)