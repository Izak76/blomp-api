from requests_toolbelt import MultipartEncoderMonitor
from .monitor import Monitor


class UploadMonitor(Monitor):
    def _update(self, loaded: MultipartEncoderMonitor):
        self.__loaded = loaded.bytes_read