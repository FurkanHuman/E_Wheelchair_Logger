import time
from .SDCardHandler import SDCardHandler


class SDLogger():
    def __init__(self, sd_ch: SDCardHandler):
        self.sd_ch = sd_ch
        self.file_name: str = "log"
        self.index: int = 0
        self.f_extension: str = ".txt"
        self.full_path: str = f"sd/{self.file_name}_L{self.index}{self.f_extension}"
        self.log_start()
        time.sleep(1)

    def log_start(self):
        if not self.sd_ch.is_file_exists(self.full_path):
            _, self.index = self.sd_ch.log(
                self.full_path, "Log File Created", self.index)

        _, self.index = self.sd_ch.log(
            self.full_path, "Log System Started", self.index)
        return _

    def e_log(self, e: Exception, comment: str):
        error_str: str = f"Exception: {e} : {comment}"

        _, self.index = self.sd_ch.log(full_path=self.full_path,
                                       index=self.index,
                                       data_str=error_str)
        return _

    def c_log(self, comment: str):
        _, self.index = self.sd_ch.log(full_path=self.full_path,
                                       index=self.index,
                                       data_str=comment)
        return _
