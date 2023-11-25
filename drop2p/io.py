import os
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
        self.file = open(filepath, 'rb')


    def read(self, size: int) -> bytes:
        return self.file.read(size)


    def size(self) -> int:
        return os.path.getsize(self.filepath)


    def close(self):
        self.file.close()


class FileOutputStream:
    def __init__(self, filepath: str):
        self.file = open(filepath, 'wb')


    def write(self, data: bytes):
        self.file.write(data)


    def close(self):
        self.file.close()