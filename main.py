import fire
import logging
import tkinter as tk
import tkinter.ttk
import tkinter.filedialog
from drop2p.client import Client, Progress


class App(tk.Frame):
    def __init__(self, master: tk.Tk, host: str, port: int):
        super().__init__(master)
        self.pack()
        self.client = Client(host, port, self._on_send_progress, self._on_recv_progress)
        
        self._join_room_frame()
        self._upload_download_frame()


    def _join_room_frame(self):
        vertical = tk.Frame(padx=10, pady=10, highlightbackground='gray', highlightthickness=2)
        vertical.pack(side=tk.LEFT, fill='y')

        self.room_value = tk.StringVar(value='Enter room id')
        self.status_value = tk.StringVar()

        tk.Entry(vertical, width=10, textvariable=self.room_value).pack(side=tk.TOP)
        tk.Button(vertical, text='Join', padx=3, pady=3, command=self._join_room).pack(side=tk.TOP)
        tk.Label(vertical, width=10, wraplength=100, justify='left', textvariable=self.status_value).pack(side=tk.TOP)


    def _upload_download_frame(self):
        frame = tk.Frame(padx=10, pady=10, highlightbackground='gray', highlightthickness=2)
        frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._create_upload_frame(frame)
        self._create_download_frame(frame)


    def _create_upload_frame(self, parent: tk.Frame):
        self.added_files_value = tk.StringVar()
        select_files_frame = tk.Frame(parent)
        select_files_frame.pack(side=tk.TOP, anchor=tk.W)
        self.join_button = tk.Button(select_files_frame, text='Add files', padx=3, pady=3, command=self._on_add_files)
        self.join_button.pack(side=tk.LEFT)
        tk.Label(select_files_frame, textvariable=self.added_files_value).pack(side=tk.RIGHT)

        self.upload_progress = tk.IntVar()
        self.upload_status = tk.StringVar()
        file_progress_frame = tk.Frame(parent)
        file_progress_frame.pack(side=tk.TOP, anchor=tk.W)
        tkinter.ttk.Progressbar(file_progress_frame, variable=self.upload_progress, length=200).pack(side=tk.LEFT)
        tk.Label(file_progress_frame, textvariable=self.upload_status).pack(side=tk.RIGHT)

        self.all_uploads_status = tk.StringVar()
        tk.Label(parent, textvariable=self.all_uploads_status).pack(side=tk.TOP, anchor=tk.W)


    def _create_download_frame(self, parent: tk.Frame):
        self.download_progress = tk.IntVar()
        self.download_status = tk.StringVar()
        file_progress_frame = tk.Frame(parent)
        file_progress_frame.pack(side=tk.TOP, anchor=tk.W)
        tkinter.ttk.Progressbar(file_progress_frame, variable=self.download_progress, length=200).pack(side=tk.LEFT)
        tk.Label(file_progress_frame, textvariable=self.download_status).pack(side=tk.RIGHT)

        self.all_downloads_status = tk.StringVar()
        tk.Label(parent, textvariable=self.all_downloads_status).pack(side=tk.TOP, anchor=tk.W)


    def _on_add_files(self):
        files = tkinter.filedialog.askopenfilenames()
        self.client.send_files(files)
        self.added_files_value.set(f'Added {len(files)} files')


    def _on_send_progress(self, progress: Progress):
        percent = int(100 * progress.processed_bytes / progress.file_size)
        self.upload_status.set(f'({percent}%) {progress.file}')
        self.upload_progress.set(percent)
        self.all_uploads_status.set(f'{progress.pending_files} pending files')


    def _on_recv_progress(self, progress: Progress):
        percent = int(100 * progress.processed_bytes / progress.file_size)
        self.download_status.set(f'({percent}%) {progress.file}')
        self.download_progress.set(percent)
        self.all_downloads_status.set(f'{progress.pending_files} pending files')


    def _join_room(self):
        self.join_button.config(state=tk.DISABLED)
        room = self.room_value.get()
        self.status_value.set(f'Joining "{room}" room...')
        self.client.start(room)


def main(host: str = '51.68.213.225', port: int = 6709):
    logging.basicConfig(level=logging.INFO)
    root = tk.Tk()
    root.title('Drop2p')
    app = App(root, host, port)
    app.mainloop()


if __name__ == '__main__':
    fire.Fire(main)
