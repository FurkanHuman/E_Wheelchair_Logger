import time
from .SDCardHandler import SDCardHandler


class SDDataLogger():
    def __init__(self, sd_ch: SDCardHandler, file_name: str, index: int = 0):
        self.sd_ch = sd_ch
        self.file_name = file_name
        self.index: int = index
        self.f_extension: str = ".csv"

    def log(self, data_str: str | bytes):
        if not self.sd_ch.current_folder:
            return False

        full_path: str = self.path_r()

        _, self.index = self.sd_ch.log(full_path=full_path,
                                       index=self.index,
                                       data_str=data_str)
        if not _:
            _, self.index = self.sd_ch.log(full_path=full_path,
                                           index=self.index,
                                           data_str=data_str)
        return _

    def path_r(self):
        if not self.sd_ch.current_folder:
            return ""
        full_path: str = f"{self.sd_ch.current_folder}/{self.file_name}_p{self.index}{self.f_extension}"
        return full_path
