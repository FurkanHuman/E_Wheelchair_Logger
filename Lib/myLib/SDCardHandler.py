import os
import gc
import machine
import time
from ..Driver.sdcard import SDCard


class SDCardHandler():
    def __init__(self, spi_id, sck, mosi, miso, cs, baudrate):

        self.WRITE_PROTECT = False
        self.FOLDER_FORMAT = "{:02d}_{:02d}_{:02d}"

        self.spi = machine.SPI(spi_id, sck=machine.Pin(sck), mosi=machine.Pin(
            mosi), miso=machine.Pin(miso), baudrate=baudrate)
        try:

            self.sd = SDCard(self.spi, cs=machine.Pin(cs), baudrate=baudrate)

            self.sd_cart_on()

        except OSError as e:
            self.WRITE_PROTECT = True
            print(f"No SD Cart!!!\nError: {e}\n")
            return

        self.current_folder = self.create_new_root_folder()

    def sd_cart_eject(self):

        self.WRITE_PROTECT = True
        os.umount("/sd")

    def sd_cart_on(self):
        os.mount(self.sd, "/sd", readonly=False)
        print("Mounted")
        self.WRITE_PROTECT = False

    def create_new_root_folder(self):
        if self.WRITE_PROTECT:
            return None

        current_date = time.localtime()

        formatted_date = self.FOLDER_FORMAT.format(
            current_date[2], current_date[1], current_date[0])

        path = f"/sd/{formatted_date}"
        if not self.is_dir_exists(path):
            try:
                os.mkdir(path)
                # log.c_log(f"{path} path created.")
            except OSError as e:
                # log.e_logger(e, "path is not created sde-002")
                print(e)
        return path

    def ls(self, directory):
        if self.WRITE_PROTECT:
            return
        print("Files and directories:")
        data = os.ilistdir(directory)
        for d in data:
            file_name = d[0]
            file_type = "D" if d[1] & 0x4000 else "F"
            size = d[3] if len(d) == 4 else -1
            print(f"({file_type}) {file_name}, Size: {size} bytes")

    def get_file_size(self, file_path: str):
        if self.WRITE_PROTECT:
            return False
        c_file_size = os.stat(file_path)[6]
        return c_file_size

    def get_latest_part_index(self, file_name, f_extension: str):
        if self.WRITE_PROTECT:
            return False

        index: int = 0
        max_index = -1

        folder_path = f"{file_name}_p{index}{f_extension}"

        for filename in os.listdir(folder_path):
            if self.is_valid_file(filename, f_extension):
                index = self.extract_part_index(filename, f_extension)
                max_index = max(max_index, index)

        return max_index

    def is_valid_file(self, file_name: str, f_extension: str):
        if self.WRITE_PROTECT:
            return False
        return file_name.startswith(file_name) and file_name.endswith(f_extension)

    def extract_part_index(self, file_name: str, f_extension: str):
        if self.WRITE_PROTECT:
            return False

        try:
            return int(file_name[len(file_name):-len(f_extension)].split("_p")[1])
        except (ValueError, IndexError):
            return False

    def is_dir_exists(self, path):
        if self.WRITE_PROTECT:
            return False
        try:
            os.listdir(path)
            return True

        except OSError as e:
            if e.errno == 2:
                return False
            else:
                raise

    def is_file_exists(self, file_path):
        if self.WRITE_PROTECT:
            return False
        try:
            with open(file_path, 'r'):
                return True
        except OSError:
            return False

    def log(self, full_path: str, data_str: str | bytes, index: int):
        if (self.WRITE_PROTECT):
            return False, index

        log_d = open(full_path, 'a')

        ts = time.time_ns()
        try:
            log_d.write(f"{ts}, {data_str}\n")
            log_d.close()
            gc.collect()

        except OSError as e:
            if e.errno == 28:
                index += 1
                self._rotation_write(path=full_path, data_str=data_str)
                gc.collect()
            return False, index

        return True, index

    def _rotation_write(self, path: str, data_str: str | bytes):
        with open(path+".rotation", 'a') as log_d:
            ts = time.time_ns()
            log_d.write(f"{ts}, {data_str}\n")
