# arinc615_loader.py - Phase 1: XML-driven backend controller for ARINC 615A-style loader

import xml.etree.ElementTree as ET
import os
from tftp_client import TftpClient  # Assumes your existing TftpClient class is imported

def parse_arinc615a_control_file(xml_path):
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

    return components

def run_upload_from_xml(xml_path, server_ip):
    print(f"\nParsing control file: {xml_path}")
    components = parse_arinc615a_control_file(xml_path)
    
    for i, comp in enumerate(components):
        print(f"\n[{i+1}/{len(components)}] Uploading component '{comp['id']}' version {comp['version']}...")
        print(f"Target Memory: {comp['target_memory']}")
        print(f"File: {comp['file_path']}")
        
        if not os.path.exists(comp['file_path']):
            print(f"❌ File not found: {comp['file_path']}")
            continue

        client = TftpClient(server_ip, log_callback=print)
        success = client.upload_file(comp['file_path'])

        if success:
            print(f"✅ Upload of '{comp['id']}' complete.")
        else:
            print(f"❌ Upload of '{comp['id']}' failed.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="ARINC 615A XML loader")
    parser.add_argument("xml", help="Path to ARINC 615A control XML file")
    parser.add_argument("ip", help="Target TFTP server IP")
    args = parser.parse_args()

    run_upload_from_xml(args.xml, args.ip)
