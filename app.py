import wx
import fire
import logging
from client import Client, Progress


class FileTransferUI(wx.Frame):
    def __init__(self, host: str, port: int, *args, **kw):
        super(FileTransferUI, self).__init__(*args, **kw)
        self.client = Client(host, port, self._on_send_progress, self._on_recv_progress)
        self.InitUI()

    def InitUI(self):
        self.splitter = wx.SplitterWindow(self)

        # Panel 1 for Textbox, Join Room, and Disconnect
        self.panel1 = wx.Panel(self.splitter)
        panel1_box = wx.BoxSizer(wx.VERTICAL)

        self.room_text = wx.TextCtrl(self.panel1, style=wx.TE_PROCESS_ENTER)
        self.room_text.SetHint("Room id")  # Placeholder for textbox

        self.join_button = wx.Button(self.panel1, label='Join Room')
        self.join_button.Bind(wx.EVT_BUTTON, self._on_join_room)
        panel1_box.Add(self.room_text, flag=wx.EXPAND | wx.ALL, border=10)
        panel1_box.Add(self.join_button, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)

        # Status label setup - place it right below the Join Room button
        self.status_label = wx.StaticText(self.panel1, label='')
        self.status_label.SetForegroundColour(wx.Colour(128, 128, 128))  # Set text color to gray
        panel1_box.Add(self.status_label, flag=wx.LEFT | wx.BOTTOM, border=10)

        panel1_box.AddStretchSpacer()  # Add a stretchable space

        self.disconnect_button = wx.Button(self.panel1, label='Disconnect')
        self.disconnect_button.Bind(wx.EVT_BUTTON, self._disconnect)
        panel1_box.Add(self.disconnect_button, flag=wx.EXPAND | wx.ALL, border=10)

        self.panel1.SetSizer(panel1_box)

        # Panel 2 for Add Files, Progress Bars, and Titles
        self.panel2 = wx.Panel(self.splitter)
        panel2_box = wx.BoxSizer(wx.VERTICAL)

        self.add_files_button = wx.Button(self.panel2, label='Add Files')
        self.add_files_button.Bind(wx.EVT_BUTTON, self._on_add_files)
        self.files_selected_label = wx.StaticText(self.panel2, label='0 files selected')
        
        hbox_add_files = wx.BoxSizer(wx.HORIZONTAL)
        hbox_add_files.Add(self.add_files_button, flag=wx.RIGHT, border=10)
        hbox_add_files.Add(self.files_selected_label, flag=wx.ALIGN_CENTER_VERTICAL)

        panel2_box.Add(hbox_add_files, flag=wx.EXPAND | wx.ALL, border=10)

        # Sending section with title above progress bar
        sending_box = wx.BoxSizer(wx.VERTICAL)
        self.sending_label = wx.StaticText(self.panel2, label='Sending (0 pending files)')
        hbox_progress1 = wx.BoxSizer(wx.HORIZONTAL)
        self.send_progress_bar = wx.Gauge(self.panel2, range=100)
        self.send_progress_label = wx.StaticText(self.panel2, label='0%')
        self.sending_file_label = wx.StaticText(self.panel2, label='')
        self.sending_file_label.SetForegroundColour(wx.Colour(100, 100, 100))
        hbox_progress1.Add(self.send_progress_bar, proportion=1, flag=wx.EXPAND)
        hbox_progress1.Add(self.send_progress_label, flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border=5)
        sending_box.Add(self.sending_label, flag=wx.LEFT | wx.BOTTOM)
        sending_box.Add(hbox_progress1, flag=wx.EXPAND)
        sending_box.Add(self.sending_file_label, flag=wx.LEFT|wx.TOP)
        panel2_box.Add(sending_box, flag=wx.EXPAND | wx.ALL, border=10)

        # Receiving section with title above progress bar
        receiving_box = wx.BoxSizer(wx.VERTICAL)
        self.receiving_label = wx.StaticText(self.panel2, label='Receiving (0 pending files)')
        hbox_progress2 = wx.BoxSizer(wx.HORIZONTAL)
        self.recv_progress_bar = wx.Gauge(self.panel2, range=100)
        self.recv_progress_label = wx.StaticText(self.panel2, label='0%')
        self.receiving_file_label = wx.StaticText(self.panel2, label='')
        self.receiving_file_label.SetForegroundColour(wx.Colour(100, 100, 100))
        hbox_progress2.Add(self.recv_progress_bar, proportion=1, flag=wx.EXPAND)
        hbox_progress2.Add(self.recv_progress_label, flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border=5)
        receiving_box.Add(self.receiving_label, flag=wx.LEFT | wx.BOTTOM)
        receiving_box.Add(hbox_progress2, flag=wx.EXPAND)
        receiving_box.Add(self.receiving_file_label, flag=wx.LEFT|wx.TOP)
        panel2_box.Add(receiving_box, flag=wx.EXPAND | wx.ALL, border=10)

        self.panel2.SetSizer(panel2_box)

        # Split the window and set the sash position
        self.splitter.SplitVertically(self.panel1, self.panel2)
        self.Bind(wx.EVT_SIZE, self._on_size)

        self.SetTitle('Drop2p')
        self.Centre()
        self.Bind(wx.EVT_CLOSE, self._on_close)
        self._disconnected_state()


    def _on_size(self, event: wx.Event):
        size = self.GetSize()
        self.splitter.SetSashPosition(int(size.x * 0.3))
        event.Skip()


    def _on_add_files(self, event: wx.Event):
        with wx.FileDialog(self, "Choose files", wildcard="All files (*.*)|*.*",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE) as fileDialog:
            assert isinstance(fileDialog, wx.FileDialog)

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return

            paths = fileDialog.GetPaths()
            self.files_selected_label.SetLabel(f'{len(paths)} files selected')
            self.client.send_files(paths)

        self.Layout()


    def _on_send_progress(self, progress: Progress):
        wx.CallAfter(self._update_send_progress, progress)


    def _update_send_progress(self, progress: Progress):
        percent = int(100 * progress.processed_bytes / progress.file_size)
        self.send_progress_label.SetLabelText(f'{percent}%')
        self.send_progress_bar.SetValue(percent)
        self.sending_label.SetLabelText(f'Sending ({progress.pending_files} pending files)')
        self.sending_file_label.SetLabelText(progress.file)
        if progress.processed_bytes == progress.file_size:
            self.send_progress_bar.SetValue(0)
            self.send_progress_label.SetLabelText('0%')
            self.sending_file_label.SetLabelText('')
        self.send_progress_bar.Update()
        self.send_progress_label.Update()
        self.sending_label.Update()
        self.sending_file_label.Update()


    def _on_recv_progress(self, progress: Progress):
        wx.CallAfter(self._update_recv_progress, progress)


    def _update_recv_progress(self, progress: Progress):
        percent = int(100 * progress.processed_bytes / progress.file_size)
        self.recv_progress_label.SetLabelText(f'{percent}%')
        self.recv_progress_bar.SetValue(percent)
        self.receiving_label.SetLabelText(f'Receiving ({progress.pending_files} pending files)')
        self.receiving_file_label.SetLabelText(progress.file)
        if progress.processed_bytes == progress.file_size:
            self.recv_progress_bar.SetValue(0)
            self.recv_progress_label.SetLabelText('0%')
            self.receiving_file_label.SetLabelText('')
        self.recv_progress_bar.Update()
        self.recv_progress_label.Update()
        self.receiving_label.Update()
        self.receiving_file_label.Update()


    def _on_join_room(self, event: wx.Event):
        room = self.room_text.GetValue()
        self.room_text.Disable()
        self.join_button.Disable()
        self._show_status(f'Joining room {room}...')
        self.client.start(room, self._on_connect_result)


    def _show_status(self, text: str):
        self.status_label.SetLabel(text)
        self.status_label.Wrap(self.panel1.GetSize().width)
        self.status_label.Layout()


    def _on_connect_result(self, is_connected: bool):
        if is_connected:
            self._connected_state()
            self._show_status('Connected!')
        else:
            self._disconnected_state()
            self._show_status('Failed to connect!')


    def _disconnect(self, event: wx.Event):
        self._disconnected_state()
        self._show_status('')
        self.client.stop()


    def _connected_state(self, connected: bool = True):
        self.disconnect_button.Enable(connected)
        self.join_button.Enable(not connected)
        self.add_files_button.Enable(connected)
        self.room_text.Enable(not connected)


    def _disconnected_state(self):
        self._connected_state(False)


    def _on_close(self, event: wx.Event):
        if self.client.is_connected():
            self.client.stop()
        self.Destroy()


def main(host: str, port: int):
    logging.basicConfig(level=logging.INFO)
    app = wx.App(False)
    frame = FileTransferUI(host, port, None)
    frame.Show(True)
    frame.Raise()
    app.MainLoop()


if __name__ == '__main__':
    fire.Fire(main)
