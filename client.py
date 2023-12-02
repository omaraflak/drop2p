import io
import os
import socket
import logging
from natpunch.client import NatPunchClient
from dataclasses import dataclass
from threading import Thread
from typing import Callable
from queue import Queue
from pysock import PySock


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
            self.pending_files.to_bytes(4, 'big') +
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
        output_directory: str = './drop2p'
    ):
        self.host = host
        self.port = port
        self.on_send_progress = on_send_progress
        self.on_recv_progress = on_recv_progress
        self.output_directory = output_directory
        self.pending_files: Queue[str] = Queue()
        self.running = False


    def start(self, room: str, on_result: Callable[[bool], None]):
        os.makedirs(self.output_directory, exist_ok=True)
        Thread(target=self._connect, args=(room, on_result)).start()


    def stop(self):
        self.running = False
        self.socket.close()
        self.pending_files.put('')


    def send_files(self, files: str):
        for file in files:
            self.pending_files.put(file)


    def is_connected(self) -> bool:
        return self.running


    def _connect(self, room: str, on_result: Callable[[bool], None]):
        sock = NatPunchClient(self.host, self.port, room).start()
        if not sock:
            on_result(False)
            return

        sock.settimeout(360)
        self.socket = PySock(sock)
        self.running = True
        Thread(target=self._send_loop).start()
        Thread(target=self._recv_loop).start()
        on_result(True)


    def _send_loop(self):
        while self.running:
            filepath = self.pending_files.get()
            if filepath == '':
                continue

            try:
                self._send_file(filepath)
            except socket.timeout:
                logging.debug('timed out')
            except socket.error as e:
                logging.error(f'error: {e}')
                self.running = False


    def _send_file(self, filepath: str):
        filename = os.path.basename(filepath)
        header = Header(filename, self.pending_files.qsize())
        self.socket.send(header.to_bytes())
        with io.FileIO(filepath, 'rb') as file:
            self.socket.send_stream(
                file,
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
        header = Header.from_bytes(self.socket.recv())
        with io.FileIO(os.path.join(self.output_directory, header.filename), 'wb') as file:
            self.socket.recv_stream(
                file,
                lambda received, size: self.on_recv_progress(Progress(header.filename, received, size, header.pending_files))
            )
