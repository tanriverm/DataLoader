# gui_client.py - Enhanced GUI with box selection, ping check, progress bars, and summary

import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import threading
import xml.etree.ElementTree as ET
import os
import subprocess
from tftp_client import TftpClient

class TftpGuiApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TFTP Loader GUI")
        self.filepath = None
        self.is_xml_mode = False
        self.box_ips = {
            "FCC1": "127.0.0.1",
            "FCC2": "192.168.1.102",
            "FCC3": "192.168.1.103",
            "FCC4": "192.168.1.104"
        }
        self.selected_boxes = {}
        self.status_labels = {}

        # File selection
        self.file_label = tk.Label(root, text="No file selected")
        self.file_label.pack(pady=5)

        self.select_button = tk.Button(root, text="Select File or XML", command=self.select_file)
        self.select_button.pack(pady=5)

        # Box selection
        self.box_frame = tk.LabelFrame(root, text="Select Target FCCs")
        self.box_frame.pack(pady=5)
        for box in self.box_ips:
            var = tk.BooleanVar()
            chk = tk.Checkbutton(self.box_frame, text=box, variable=var)
            chk.pack(anchor='w')
            self.selected_boxes[box] = var
            status = tk.Label(self.box_frame, text="[Status]", fg="gray")
            status.pack(anchor='e')
            self.status_labels[box] = status

        self.ping_button = tk.Button(root, text="Ping Selected Boxes", command=self.ping_boxes)
        self.ping_button.pack(pady=5)

        self.upload_button = tk.Button(root, text="Upload", command=self.start_upload)
        self.upload_button.pack(pady=5)

        self.progress = ttk.Progressbar(root, length=300)
        self.progress.pack(pady=5)

        self.log_text = tk.Text(root, height=12, width=70)
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

    def ping_boxes(self):
        for box, var in self.selected_boxes.items():
            if var.get():
                ip = self.box_ips[box]
                reachable = self.ping_host(ip)
                color = "green" if reachable else "red"
                self.status_labels[box].config(text="Online" if reachable else "Offline", fg=color)

    def ping_host(self, ip):
        try:
            result = subprocess.run(["ping", "-n", "1", ip], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return "TTL=" in result.stdout
        except:
            return False

    def start_upload(self):
        if not self.filepath:
            messagebox.showwarning("No File", "Please select a file to upload.")
            return

        active_boxes = [box for box, var in self.selected_boxes.items() if var.get() and self.status_labels[box].cget("fg") == "green"]
        if not active_boxes:
            messagebox.showwarning("No Target", "No reachable target boxes selected.")
            return

        thread = threading.Thread(target=self.upload_thread, args=(active_boxes,))
        thread.start()

    def upload_thread(self, targets):
        self.progress['value'] = 0
        self.log("Starting upload to: " + ", ".join(targets))

        result_summary = {}

        for box in targets:
            self.log(f"\n--- Uploading to {box} ---")
            ip = self.box_ips[box]
            success = False
            if self.is_xml_mode:
                success = self.upload_from_xml(self.filepath, ip)
            else:
                client = TftpClient(ip, log_callback=self.log, progress_callback=self.update_progress)
                success = client.upload_file(self.filepath)

            result_summary[box] = "PASS" if success else "FAIL"

        # Final summary
        self.log("\n=== Upload Summary ===")
        for box, status in result_summary.items():
            self.log(f"{box}: {status}")

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
                    return False

                client = TftpClient(server_ip, log_callback=self.log, progress_callback=self.update_progress)
                success = client.upload_file(comp['file_path'])

                if not success:
                    self.log(f"❌ Upload of '{comp['id']}' failed.")
                    return False

                self.log(f"✅ Upload of '{comp['id']}' complete.")

            return True

        except Exception as e:
            self.log(f"⚠️ XML Upload error: {e}")
            return False

if __name__ == "__main__":
    root = tk.Tk()
    app = TftpGuiApp(root)
    root.mainloop()
