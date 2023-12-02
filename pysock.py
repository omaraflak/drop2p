import io
import socket
import select
from typing import Optional, Callable


OnProgress = Callable[[int, int], None]


class PySock:
    def __init__(
        self,
        sock: socket.socket,
        max_chunk: int = 1 << 20,
        size_bytes: int = 4
    ):
        self.sock = sock
        self.max_chunk = max_chunk
        self.size_bytes = size_bytes


    def close(self):
        self.sock.close()


    def send(self, data: bytes):
        self.sock.sendall(self._i2b(len(data)) + data)


    def send_stream(self, stream: io.IOBase, on_progress: Optional[OnProgress] = None):
        data_size = PySock._stream_size(stream)
        self.sock.sendall(self._i2b(data_size))
        total_sent = 0
        while True:
            tmp = stream.read(self.max_chunk)
            if tmp == b'':
                break
            self.sock.sendall(tmp)
            total_sent += len(tmp)
            if on_progress:
                on_progress(total_sent, data_size)


    def recv(self) -> bytes:
        size = self._b2i(self._recv_all(self.size_bytes))
        return self._recv_all(size)


    def recv_stream(self, stream: io.IOBase, on_progress: Optional[OnProgress] = None):
        size = self._b2i(self._recv_all(self.size_bytes))
        received = 0
        while received != size:
            chunk = min(self.max_chunk, size - received)
            data = self._recv_all(chunk)
            stream.write(data)
            received += len(data)
            if on_progress:
                on_progress(received, size)


    def _i2b(self, n: int) -> bytes:
        return n.to_bytes(self.size_bytes, 'big')


    def _b2i(self, b: bytes) -> int:
        return int.from_bytes(b, 'big')


    def _recv_all(self, size: int) -> bytes:
        data = bytearray()
        while len(data) != size:
            if not PySock._has_data(self.sock):
                continue
            chunk = min(self.max_chunk, size - len(data))
            received = self.sock.recv(chunk)
            if received == b'':
                raise socket.error('socket closed!')
            data.extend(received)
        return bytes(data)


    @staticmethod
    def _has_data(sock: socket.socket) -> bool:
        r, _, _ = select.select([sock], [], [])
        return len(r) > 0


    @staticmethod
    def _stream_size(file: io.IOBase) -> int:
        current = file.tell()
        size = file.seek(0, io.SEEK_END)
        file.seek(current)
        return size - current
