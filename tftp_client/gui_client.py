import socket
import threading
import tkinter as tk
import zlib
from tkinter import ttk, filedialog, scrolledtext, messagebox

# === TftpClient class with progress and logging callbacks ===
class TftpClient:
    def __init__(self, server_ip, server_port=69, timeout=2, retries=5,
                 log_callback=None, progress_callback=None):
        self.server_ip = server_ip
        self.server_port = server_port
        self.timeout = timeout
        self.retries = retries
        self.log_callback = log_callback or (lambda msg: None)
        self.progress_callback = progress_callback or (lambda current, total: None)

    def log(self, msg):
        self.log_callback(msg)

    def send_wrq(self, sock, filename, mode="octet", options=None):
        options = options or {}
        rrq_packet = b"\x00\x02" + filename.encode() + b"\x00" + mode.encode() + b"\x00"
        for k, v in options.items():
            rrq_packet += k.encode() + b"\x00" + str(v).encode() + b"\x00"
        sock.sendto(rrq_packet, (self.server_ip, self.server_port))
        self.log(f"Sent WRQ for file '{filename}'")

    def send_data_block(self, sock, block_num, data, addr):
        header = b"\x00\x03" + block_num.to_bytes(2, 'big')
        sock.sendto(header + data, addr)
        self.log(f"Sent DATA block {block_num} ({len(data)} bytes)")

    def receive_ack(self, sock, expected_block):
        try:
            data, _ = sock.recvfrom(516)
            if len(data) >= 4:
                opcode = int.from_bytes(data[0:2], 'big')
                block = int.from_bytes(data[2:4], 'big')
                if opcode == 4 and block == expected_block:
                    self.log(f"Received ACK for block {block}")
                    return True
            self.log("Unexpected or invalid ACK received")
            return False
        except socket.timeout:
            self.log(f"Timeout waiting for ACK {expected_block}")
            return False

    def upload_file(self, filepath):
        try:
            filesize = 0
            with open(filepath, "rb") as f:
                f.seek(0, 2)
                filesize = f.tell()

            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(self.timeout)

            filename = filepath.split('/')[-1]

            # Send WRQ
            self.send_wrq(sock, filename)
            # Wait for ACK block 0
            for _ in range(self.retries):
                if self.receive_ack(sock, 0):
                    break
                else:
                    self.send_wrq(sock, filename)
            else:
                self.log("Failed to receive ACK for WRQ, aborting.")
                sock.close()
                return False

            with open(filepath, "rb") as f:
                block_num = 1
                total_blocks = (filesize + 511) // 512
                crc = 0
                while True:
                    data = f.read(512)
                    if not data:
                        break
                    # Update CRC32 with this block's data
                    crc = zlib.crc32(data, crc)
                    
                    for attempt in range(1, self.retries + 1):
                        self.send_data_block(sock, block_num, data, (self.server_ip, self.server_port))
                        if self.receive_ack(sock, block_num):
                            break
                        else:
                            self.log(f"Retry block {block_num} (attempt {attempt})")
                    else:
                        self.log(f"Failed to send block {block_num} after {self.retries} attempts.")
                        sock.close()
                        return False
                    # Update progress
                    self.progress_callback(block_num, total_blocks)
                    block_num += 1

            # Send CRC packet (opcode 0x10 + 4 bytes CRC32)
            crc_packet = bytearray()
            crc_packet += b'\x00' + b'\x10'  # opcode 0x10
            crc_packet += crc.to_bytes(4, 'big')
            sock.sendto(crc_packet, (self.server_ip, self.server_port))
            self.log(f"Sent CRC32: 0x{crc:08X}")

            sock.close()
            self.log("✅ File transfer complete.")
            return True

        except Exception as e:
            self.log(f"Exception: {e}")
            return False


# === GUI application ===
class TftpGuiApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TFTP Client GUI (ARINC 615 Loader Demo)")
        self.geometry("600x400")

        # Server IP entry
        tk.Label(self, text="TFTP Server IP:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.ip_entry = tk.Entry(self)
        self.ip_entry.insert(0, "127.0.0.1")
        self.ip_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        # Logical device combo
        tk.Label(self, text="Logical Device:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.device_var = tk.StringVar(value="FCC1")
        devices = ["FCC1", "FCC2", "FCC3", "FCC4"]
        self.device_combo = ttk.Combobox(self, textvariable=self.device_var, values=devices, state="readonly")
        self.device_combo.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        # File selection
        tk.Label(self, text="File to Upload:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.file_path_var = tk.StringVar()
        self.file_entry = tk.Entry(self, textvariable=self.file_path_var)
        self.file_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
        self.browse_btn = tk.Button(self, text="Browse...", command=self.browse_file)
        self.browse_btn.grid(row=2, column=2, padx=5, pady=5)

        # Start button
        self.start_btn = tk.Button(self, text="Start Upload", command=self.start_upload)
        self.start_btn.grid(row=3, column=1, pady=10)

        # Progress bar and label
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self, maximum=100, variable=self.progress_var)
        self.progress_bar.grid(row=4, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        self.progress_label = tk.Label(self, text="Progress: 0%")
        self.progress_label.grid(row=5, column=0, columnspan=3, sticky="ew", padx=5)

        # Log output box
        tk.Label(self, text="Log Output:").grid(row=6, column=0, sticky="w", padx=5, pady=5)
        self.log_box = scrolledtext.ScrolledText(self, height=8, state="disabled")
        self.log_box.grid(row=7, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)

        # Configure column weights for resizing
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(7, weight=1)

        # Disable Start button if no file selected
        self.file_path_var.trace_add("write", self.toggle_start_button)
        self.toggle_start_button()

    def toggle_start_button(self, *args):
        if self.file_path_var.get():
            self.start_btn.config(state="normal")
        else:
            self.start_btn.config(state="disabled")

    def browse_file(self):
        file_path = filedialog.askopenfilename(title="Select file to upload")
        if file_path:
            self.file_path_var.set(file_path)

    def log(self, msg):
        self.log_box.configure(state="normal")
        self.log_box.insert(tk.END, msg + "\n")
        self.log_box.see(tk.END)
        self.log_box.configure(state="disabled")

    def update_progress(self, current_block, total_blocks):
        percent = (current_block / total_blocks) * 100 if total_blocks else 0
        self.progress_var.set(percent)
        self.progress_label.config(text=f"Progress: {percent:.1f}%")

    def start_upload(self):
        filepath = self.file_path_var.get()
        server_ip = self.ip_entry.get()
        # You can add device logic here for filename modifications if needed
        self.log("Starting upload...")

        self.start_btn.config(state="disabled")
        self.thread = threading.Thread(target=self.upload_thread, args=(server_ip, filepath), daemon=True)
        self.thread.start()

    def upload_thread(self, server_ip, filepath):
        client = TftpClient(server_ip,
                            log_callback=self.log,
                            progress_callback=self.update_progress)
        success = client.upload_file(filepath)
        if success:
            self.log("Upload completed successfully!")
        else:
            self.log("Upload failed.")
        self.start_btn.config(state="normal")


if __name__ == "__main__":
    app = TftpGuiApp()
    app.mainloop()
