import os
import logging
from typing import Protocol


class InputStream(Protocol):
    def read(self, size: int) -> bytes:
        pass


    def size(self) -> int:
        pass


class OutputStream(Protocol):
    def write(self, data: bytes):
        pass


class FileInputStream:
    def __init__(self, filepath: str):
        self.filepath = filepath


    def read(self, size: int) -> bytes:
        return self.file.read(size)


    def size(self) -> int:
        return os.path.getsize(self.filepath)


    def close(self):
        self.file.close()


    def __enter__(self) -> 'FileInputStream':
        self.file = open(self.filepath, 'rb')
        return self


    def __exit__(self, err_type, err_value, traceback) -> bool:
        if err_type == FileNotFoundError:
            logging.error(err_value)
            self.file.close()
            return True
        return False


class FileOutputStream:
    def __init__(self, filepath: str):
        self.filepath = filepath


    def write(self, data: bytes):
        self.file.write(data)


    def close(self):
        self.file.close()


    def __enter__(self) -> 'FileOutputStream':
        self.file = open(self.filepath, 'wb')
        return self


    def __exit__(self, err_type, err_value, traceback) -> bool:
        if err_type == FileExistsError:
            logging.error(err_value)
            self.file.close()
            return True
        return False