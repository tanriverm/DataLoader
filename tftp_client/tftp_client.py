import socket
import struct
import zlib
import os

class TftpClient:
    OPCODE_WRQ = 2
    OPCODE_DATA = 3
    OPCODE_ACK = 4
    BLOCK_SIZE = 512
    MAX_RETRIES = 5
    TIMEOUT = 3.0

    def __init__(self, server_ip, server_port=69):
        self.server_ip = server_ip
        self.server_port = server_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(self.TIMEOUT)
        self.server_addr = (server_ip, server_port)

    def send_wrq(self, filename, mode="octet"):
        payload = filename.encode() + b'\x00' + mode.encode() + b'\x00'
        packet = struct.pack("!H", self.OPCODE_WRQ) + payload
        self.sock.sendto(packet, self.server_addr)

    def send_data(self, block_num, data):
        packet = struct.pack("!HH", self.OPCODE_DATA, block_num) + data
        self.sock.sendto(packet, self.server_addr)
        print(f"Sent DATA block {block_num} (attempt 1)")

    def wait_for_ack(self, expected_block):
        while True:
            response, addr = self.sock.recvfrom(1024)
            opcode, block = struct.unpack("!HH", response[:4])
            if opcode == self.OPCODE_ACK and block == expected_block:
                print(f"Received ACK for block {block}")
                return True

    def send_file(self, filename):
        block_num = 1
        last_block_size = self.BLOCK_SIZE
        crc32 = 0

        self.send_wrq(os.path.basename(filename))
        self.wait_for_ack(0)

        with open(filename, "rb") as f:
            while True:
                data = f.read(self.BLOCK_SIZE)
                if not data:
                    break

                crc32 = zlib.crc32(data, crc32)

                retries = 0
                while retries < self.MAX_RETRIES:
                    self.send_data(block_num, data)
                    try:
                        if self.wait_for_ack(block_num):
                            break
                    except socket.timeout:
                        retries += 1
                        print(f"Retry block {block_num}")
                else:
                    raise Exception(f"Failed to send block {block_num} after {self.MAX_RETRIES} attempts.")

                last_block_size = len(data)
                block_num += 1

        if last_block_size == self.BLOCK_SIZE:
            retries = 0
            while retries < self.MAX_RETRIES:
                self.send_data(block_num, b"")
                try:
                    if self.wait_for_ack(block_num):
                        print("✅ Final empty block acknowledged")
                        break
                except socket.timeout:
                    retries += 1
                    print(f"Retry final empty block {block_num}")
            else:
                raise Exception("Failed to send final empty block")

        print("✅ File transfer complete.")
        # ✅ Send CRC32 in custom block (opcode 0x10)
        crc_opcode = 0x10
        crc_packet = struct.pack("!H", crc_opcode) + struct.pack(">I", crc32)
        self.sock.sendto(crc_packet, self.server_addr)
        print(f"✅ CRC32 sent to server in custom block: 0x{crc32:08X}")

if __name__ == "__main__":
    client = TftpClient("127.0.0.1", 69)
    client.send_file("test_input.sre")
