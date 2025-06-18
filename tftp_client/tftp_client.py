# tftp_client.py - Standalone reusable TFTP client with CRC32 and callback support

import socket
import zlib

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

                    self.progress_callback(block_num, total_blocks)
                    block_num += 1

            # Send CRC32 packet with custom opcode 0x10
            crc_packet = bytearray()
            crc_packet += b'\x00' + b'\x10'
            crc_packet += crc.to_bytes(4, 'big')
            sock.sendto(crc_packet, (self.server_ip, self.server_port))
            self.log(f"Sent CRC32: 0x{crc:08X}")

            sock.close()
            self.log("✅ File transfer complete.")
            return True

        except Exception as e:
            self.log(f"Exception: {e}")
            return False
