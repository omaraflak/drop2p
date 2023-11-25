import fire
import logging
import tkinter as tk
import tkinter.ttk
import tkinter.filedialog
from drop2p.client import Client, Progress


class App(tk.Frame):
    def __init__(self, master: tk.Tk, host: str, port: int):
        super().__init__(master)
        self.master = master
        self.pack()
        self.client = Client(host, port, self._on_send_progress, self._on_recv_progress)
        master.protocol("WM_DELETE_WINDOW", self._on_close)
        
        self._join_room_frame()
        self._upload_download_frame()


    def _on_close(self):
        if self.client.is_connected():
            self.client.stop()
        self.master.destroy()


    def _join_room_frame(self):
        vertical = tk.Frame(padx=10, pady=10, highlightbackground='gray', highlightthickness=2)
        vertical.pack(side=tk.LEFT, fill='y')

        self.room_value = tk.StringVar(value='Enter room id')
        self.status_value = tk.StringVar()

        self.room_textbox = tk.Entry(vertical, width=10, textvariable=self.room_value)
        self.room_textbox.pack(side=tk.TOP)
        self.join_button = tk.Button(vertical, text='Join', padx=3, pady=3, command=self._join_room)
        self.join_button.pack(side=tk.TOP)
        tk.Label(vertical, width=10, wraplength=100, justify='left', textvariable=self.status_value).pack(side=tk.TOP)

        self.disconnect_button = tk.Button(vertical, text='Disconnect', padx=3, pady=3, command=self._disconnect)
        self.disconnect_button.pack(side=tk.BOTTOM)
        self.disconnect_button.config(state=tk.DISABLED)


    def _upload_download_frame(self):
        frame = tk.Frame(padx=10, pady=10, highlightbackground='gray', highlightthickness=2)
        frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._create_upload_frame(frame)
        self._create_download_frame(frame)


    def _create_upload_frame(self, parent: tk.Frame):
        self.added_files_value = tk.StringVar()
        select_files_frame = tk.Frame(parent)
        select_files_frame.pack(side=tk.TOP, anchor=tk.W)
        tk.Button(select_files_frame, text='Add files', padx=3, pady=3, command=self._on_add_files).pack(side=tk.LEFT)
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
        if progress.processed_bytes == progress.file_size:
            self.upload_progress.set(0)
            self.upload_status.set('')


    def _on_recv_progress(self, progress: Progress):
        percent = int(100 * progress.processed_bytes / progress.file_size)
        self.download_status.set(f'({percent}%) {progress.file}')
        self.download_progress.set(percent)
        self.all_downloads_status.set(f'{progress.pending_files} pending files')
        if progress.processed_bytes == progress.file_size:
            self.download_progress.set(0)
            self.download_status.set('')


    def _join_room(self):
        self.join_button.config(state=tk.DISABLED)
        self.room_textbox.config(state=tk.DISABLED)
        room = self.room_value.get()
        self.status_value.set(f'Joining "{room}" room...')
        self.update()
        if self.client.start(room):
            self.disconnect_button.config(state=tk.NORMAL)
            self.status_value.set(f'Connected!')
        else:
            self.join_button.config(state=tk.NORMAL)
            self.room_textbox.config(state=tk.NORMAL)            
            self.status_value.set(f'Could not connect.')


    def _disconnect(self):
        self.client.stop()
        self.join_button.config(state=tk.NORMAL)
        self.room_textbox.config(state=tk.NORMAL)
        self.disconnect_button.config(state=tk.DISABLED)
        self.status_value.set('')


def main(host: str = '51.68.213.225', port: int = 6709):
    logging.basicConfig(level=logging.INFO)
    root = tk.Tk()
    root.title('Drop2p')
    app = App(root, host, port)
    app.mainloop()


if __name__ == '__main__':
    fire.Fire(main)
