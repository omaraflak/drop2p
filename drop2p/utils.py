import socket
from typing import Optional, Callable
from drop2p.io import InputStream, OutputStream


MAX_CHUNK = 1 << 18
OnProgress = Callable[[int, int], None]



def socket_send(sock: socket.socket, data: bytes):
    sock.sendall(len(data).to_bytes(4, 'big') + data)


def socket_send_stream(sock: socket.socket, stream: InputStream, on_progress: Optional[OnProgress] = None):
    data_size = stream.size()
    sock.sendall(data_size.to_bytes(4, 'big'))

    total_sent = 0
    while True:
        tmp = stream.read(MAX_CHUNK)
        if tmp == b'':
            break
        sock.sendall(tmp)
        total_sent += len(tmp)
        if on_progress:
            on_progress(total_sent, data_size)


def socket_recv(sock: socket.socket) -> bytes:
    size_bytes = _recv_all(sock, 4)
    size = int.from_bytes(size_bytes, 'big')
    return _recv_all(sock, size)


def socket_recv_stream(sock: socket.socket, stream: OutputStream, on_progress: Optional[OnProgress] = None):
    size_bytes = _recv_all(sock, 4)
    size = int.from_bytes(size_bytes, 'big')
    received = 0
    while received != size:
        chunk = min(MAX_CHUNK, size - received)
        data = _recv_all(sock, chunk)
        stream.write(data)
        received += len(data)
        if on_progress:
            on_progress(received, size)

    
def _recv_all(sock: socket.socket, size: int) -> bytes:
    data = bytearray()
    while len(data) != size:
        chunk = min(MAX_CHUNK, size - len(data))
        received = sock.recv(chunk)
        if received == b'':
            raise socket.error('socket closed!')
        data.extend(received)
    return bytes(data)
