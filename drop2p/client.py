import os
import time
import errno
import socket
import logging
from natpunch.client import NatPunchClient
from collections import deque
from typing import Optional, Callable
from threading import Thread
from dataclasses import dataclass
from drop2p.io import FileInputStream, FileOutputStream
from drop2p.utils import socket_send, socket_send_stream, socket_recv, socket_recv_stream


@dataclass
class Progress:
    file: str
    processed_bytes: int
    file_size: int
    pending_files: int



@dataclass
class Header:
    filename: str
    pending_files: int


    def to_bytes(self) -> bytes:
        return (
            len(self.pending_files).to_bytes(4, 'big') +
            self.filename.encode()
        )


    @classmethod
    def from_bytes(cls, header: bytes) -> 'Header':
        pending_files = int.from_bytes(header[:4], 'big')
        filename = header[4:].decode()
        return Header(filename, pending_files)


OnProgress = Callable[[Progress], None]


class Client:
    def __init__(
        self,
        host: str,
        port: int,
        on_send_progress: OnProgress,
        on_recv_progress: OnProgress,
        output_directory: str = './downloads'
    ):
        self.host = host
        self.port = port
        self.on_send_progress = on_send_progress
        self.on_recv_progress = on_recv_progress
        self.pending_files: deque[str] = deque()
        self.output_directory = output_directory
        self.running = True


    def start(self, room: str) -> bool:
        self.socket = NatPunchClient(self.host, self.port, room).start()
        if not self.socket:
            return False
        self.socket.settimeout(360)
        Thread(target=self._send_loop).start()
        Thread(target=self._recv_loop).start()
        return True


    def stop(self):
        self.running = False


    def send_files(self, files: str):
        self.pending_files.extend(files)


    def _send_loop(self):
        while self.running:
            if not self.pending_files:
                time.sleep(3)
                continue

            filepath = self.pending_files.popleft()
            try:
                self._send_file(filepath)
            except FileNotFoundError as e:
                logging.error(f'File not found: {e}')
            except socket.timeout:
                logging.debug('timed out')
            except socket.error as e:
                logging.error(f'error: {e}')
                self.running = False


    def _send_file(self, filepath: str):
        filename = os.path.basename(filepath)
        header = Header(filename, len(self.pending_files))
        socket_send(self.socket, header.to_bytes())
        fis = FileInputStream(filepath)
        socket_send_stream(
            self.socket,
            fis,
            lambda sent, size: self.on_send_progress(Progress(filename, sent, size, header.pending_files))
        )


    def _recv_loop(self):
        while self.running:
            try:
                self._recv_file()
            except socket.timeout:
                logging.debug('timed out')
            except socket.error as e:
                logging.error(f'error: {e}')
                self.running = False


    def _recv_file(self):
        header = Header.from_bytes(socket_recv(self.socket))
        fos = FileOutputStream(os.path.join(self.output_directory, header.filename))
        socket_recv_stream(
            self.socket,
            fos,
            lambda received, size: self.on_recv_progress(Progress(header.filename, received, size, header.pending_files))
        )
        fos.close()
