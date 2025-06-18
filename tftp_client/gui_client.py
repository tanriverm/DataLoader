# gui_client.py - GUI for TFTP client with progress and diagnostics

import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import threading
from tftp_client import TftpClient
import os

class TftpGuiApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TFTP Loader GUI")
        self.filepath = None

        # Widgets
        self.file_label = tk.Label(root, text="No file selected")
        self.file_label.pack(pady=5)

        self.select_button = tk.Button(root, text="Select File", command=self.select_file)
        self.select_button.pack(pady=5)

        self.ip_entry = tk.Entry(root)
        self.ip_entry.insert(0, "127.0.0.1")
        self.ip_entry.pack(pady=5)

        self.upload_button = tk.Button(root, text="Upload", command=self.start_upload)
        self.upload_button.pack(pady=5)

        self.progress = ttk.Progressbar(root, length=300)
        self.progress.pack(pady=5)

        self.log_text = tk.Text(root, height=10, width=50)
        self.log_text.pack(pady=5)

    def select_file(self):
        path = filedialog.askopenfilename()
        if path:
            self.filepath = path
            self.file_label.config(text=os.path.basename(path))

    def log(self, msg):
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)

    def update_progress(self, current, total):
        percent = int((current / total) * 100)
        self.progress['value'] = percent
        self.root.update_idletasks()

    def start_upload(self):
        if not self.filepath:
            messagebox.showwarning("No File", "Please select a file to upload.")
            return

        ip = self.ip_entry.get().strip()
        if not ip:
            messagebox.showwarning("No IP", "Please enter the TFTP server IP address.")
            return

        thread = threading.Thread(target=self.upload_thread, args=(ip,))
        thread.start()

    def upload_thread(self, ip):
        self.progress['value'] = 0
        self.log("Starting upload...")
        client = TftpClient(ip, log_callback=self.log, progress_callback=self.update_progress)
        success = client.upload_file(self.filepath)
        if success:
            self.log("✅ Upload complete.")
        else:
            self.log("❌ Upload failed.")

if __name__ == "__main__":
    root = tk.Tk()
    app = TftpGuiApp(root)
    root.mainloop()
