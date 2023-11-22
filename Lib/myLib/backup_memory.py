SECRETS_FOLDER: str = "/Secrets/"


class backup_memory:
    def __init__(self, file_name: str, reset: bool = False):

        self.file_name = SECRETS_FOLDER + file_name

        if reset:
            self.__one_shot_write("")

        self.temp = int(self.__one_shot_read())

        self.temp += 1

        self.__one_shot_write(self.temp)

    def __one_shot_read(self):
        try:
            with open(self.file_name, 'r') as f:
                return f.read()
        except Exception as e:
            print(e)
            return "0"

    def __one_shot_write(self, new_value):
        try:
            with open(self.file_name, 'w') as f:
                f.write(str(new_value))
        except Exception as e:
            print(e)

    def get_one_shot_value(self):
        return self.temp
