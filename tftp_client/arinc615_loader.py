# arinc615_loader.py - Main data loader logic including TFTP + ARINC 615A control protocol

import socket
import json
import os
from tftp_client import TftpClient

class ControlClient:
    def __init__(self, ip, port=61500, timeout=5):
        self.ip = ip
        self.port = port
        self.timeout = timeout

    def send_command(self, command_name, **params):
        message = json.dumps({"command": command_name, **params}).encode("utf-8")
        try:
            with socket.create_connection((self.ip, self.port), timeout=self.timeout) as sock:
                sock.sendall(message)
                response = sock.recv(1024)
                return json.loads(response.decode("utf-8"))
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}

    def init_load(self, device_id, session_id):
        return self.send_command("INIT_LOAD", device=device_id, session_id=session_id)

    def send_lse(self, lse_id, version, memory, file, crc32):
        return self.send_command(
            "SEND_LSE",
            lse_id=lse_id,
            version=version,
            memory=memory,
            file_name=file,
            crc32=crc32
        )

    def verify_lse(self, lse_id):
        return self.send_command("VERIFY_LSE", lse_id=lse_id)

    def commit_load(self, session_id):
        return self.send_command("COMMIT_LOAD", session_id=session_id)

    def abort(self, reason="User request"):
        return self.send_command("ABORT", reason=reason)

    def report_status(self):
        return self.send_command("REPORT_STATUS")

    def get_device_info(self):
        return self.send_command("GET_DEVICE_INFO")

class Arinc615Loader:
    def __init__(self, server_ip):
        self.server_ip = server_ip
        self.tftp = TftpClient(server_ip)
        self.control = ControlClient(server_ip)

    def upload_one_component(self, device_id, lse_id, version, memory, file_path, crc32, session_id):
        print(f"\n[1/4] INIT_LOAD ({device_id})")
        res = self.control.init_load(device_id, session_id)
        print(res)
        if res.get("status") != "OK":
            return res

        print(f"[2/4] SEND_LSE ({lse_id})")
        res = self.control.send_lse(lse_id, version, memory, os.path.basename(file_path), crc32)
        print(res)
        if res.get("status") != "OK":
            return res

        print("[3/4] TFTP File Transfer")
        self.tftp.upload_file(file_path)

        print(f"[4/4] VERIFY_LSE and COMMIT")
        res = self.control.verify_lse(lse_id)
        print(res)
        if res.get("status") != "OK":
            return res

        res = self.control.commit_load(session_id)
        print(res)
        return res

    def run_upload_from_xml(self, xml_path, session_id):
        print(f"Parsing control file: {xml_path}")
        import xml.etree.ElementTree as ET
        tree = ET.parse(xml_path)
        root = tree.getroot()

        for comp in root.findall("component"):
            lse_id = comp.get("lse")
            device_id = comp.get("device")
            version = comp.get("version")
            file_path = comp.get("file")
            memory = comp.get("memory")
            crc32 = comp.get("crc32")

            print(f"\nUploading component '{lse_id}' version {version}...")
            print(f"Target Memory: {memory}")
            print(f"File: {file_path}")

            result = self.upload_one_component(device_id, lse_id, version, memory, file_path, crc32, session_id)
            print("Result:", result)

# Entry point test
# This main function is only used for command-line testing (e.g., running python arinc615_loader.py --xml ... --ip ... directly).
# if __name__ == '__main__':
#    import argparse
#    parser = argparse.ArgumentParser()
#    parser.add_argument("--xml", required=True, help="Path to load plan XML file")
#    parser.add_argument("--ip", required=True, help="Target IP address")
#    parser.add_argument("--session", type=int, default=1234, help="Session ID")
#    args = parser.parse_args()

#    loader = Arinc615Loader(args.ip)
#    loader.run_upload_from_xml(args.xml, args.session)
