# gui_client.py - GUI for TFTP client with progress and diagnostics (single and XML multi-file mode)

import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import threading
import xml.etree.ElementTree as ET
import os
from tftp_client import TftpClient

class TftpGuiApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TFTP Loader GUI")
        self.filepath = None
        self.is_xml_mode = False

        # Widgets
        self.file_label = tk.Label(root, text="No file selected")
        self.file_label.pack(pady=5)

        self.select_button = tk.Button(root, text="Select File or XML", command=self.select_file)
        self.select_button.pack(pady=5)

        self.ip_entry = tk.Entry(root)
        self.ip_entry.insert(0, "127.0.0.1")
        self.ip_entry.pack(pady=5)

        self.upload_button = tk.Button(root, text="Upload", command=self.start_upload)
        self.upload_button.pack(pady=5)

        self.progress = ttk.Progressbar(root, length=300)
        self.progress.pack(pady=5)

        self.log_text = tk.Text(root, height=10, width=60)
        self.log_text.pack(pady=5)

    def select_file(self):
        path = filedialog.askopenfilename(filetypes=[("All files", "*.*"), ("XML", "*.xml"), ("SRE Files", "*.sre")])
        if path:
            self.filepath = path
            self.file_label.config(text=os.path.basename(path))
            self.is_xml_mode = path.lower().endswith(".xml")

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

        if self.is_xml_mode:
            self.upload_from_xml(self.filepath, ip)
        else:
            client = TftpClient(ip, log_callback=self.log, progress_callback=self.update_progress)
            success = client.upload_file(self.filepath)
            if success:
                self.log("✅ Upload complete.")
            else:
                self.log("❌ Upload failed.")

    def upload_from_xml(self, xml_path, server_ip):
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            components = []
            for sw in root.findall('.//SoftwareComponent'):
                sw_id = sw.get('id')
                version = sw.get('version')
                target_mem = sw.get('targetMemory')
                file_elem = sw.find('File')
                if file_elem is None:
                    continue
                file_name = file_elem.get('name')
                file_path = os.path.join(os.path.dirname(xml_path), file_name)
                crc_expected = file_elem.get('crc32')

                components.append({
                    'id': sw_id,
                    'version': version,
                    'target_memory': target_mem,
                    'file_path': file_path,
                    'crc32': crc_expected
                })

            for i, comp in enumerate(components):
                self.log(f"\n[{i+1}/{len(components)}] Uploading '{comp['id']}' version {comp['version']}...")
                self.log(f"Target Memory: {comp['target_memory']}")
                self.log(f"File: {comp['file_path']}")

                if not os.path.exists(comp['file_path']):
                    self.log(f"❌ File not found: {comp['file_path']}")
                    continue

                client = TftpClient(server_ip, log_callback=self.log, progress_callback=self.update_progress)
                success = client.upload_file(comp['file_path'])

                if success:
                    self.log(f"✅ Upload of '{comp['id']}' complete.")
                else:
                    self.log(f"❌ Upload of '{comp['id']}' failed.")

        except Exception as e:
            self.log(f"⚠️ XML Upload error: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = TftpGuiApp(root)
    root.mainloop()
