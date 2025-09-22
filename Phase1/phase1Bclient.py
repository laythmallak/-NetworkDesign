# Phase 2: UDP file sender (RDT 1.0 with pacing fix)
import os
import math
import time
import socket
import struct

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5051
MAX_PAYLOAD = 1024

META_HDR_FMT = ">B I I H"
DATA_HDR_FMT = ">B I H"

TYPE_META = 0
TYPE_DATA = 1

def make_pkt(ptype, **kw):
    if ptype == TYPE_META:
        file_size, total_pkts = kw["file_size"], kw["total_pkts"]
        name_bytes = kw["file_name"].encode("utf-8")
        hdr = struct.pack(META_HDR_FMT, TYPE_META, file_size, total_pkts, len(name_bytes))
        return hdr + name_bytes
    elif ptype == TYPE_DATA:
        index, payload = kw["index"], kw["payload"]
        hdr = struct.pack(DATA_HDR_FMT, TYPE_DATA, index, len(payload))
        return hdr + payload
    else:
        raise ValueError("Invalid packet type")

def udt_send(sock, addr, pkt):
    sock.sendto(pkt, addr)

def rdt_send(sock, addr, file_path):
    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    total_pkts = math.ceil(file_size / MAX_PAYLOAD)

    meta = make_pkt(TYPE_META, file_name=file_name, file_size=file_size, total_pkts=total_pkts)
    udt_send(sock, addr, meta)
    print(f"[CLIENT] META sent: {file_name}, {file_size} bytes, {total_pkts} packets")

    sent = 0
    with open(file_path, "rb") as f:
        for index in range(total_pkts):
            payload = f.read(MAX_PAYLOAD)
            pkt = make_pkt(TYPE_DATA, index=index, payload=payload)
            udt_send(sock, addr, pkt)
            sent += 1
            if sent % 100 == 0 or sent == total_pkts:
                print(f"[CLIENT] Sent {sent}/{total_pkts}")
            if (index + 1) % 200 == 0:   # pacing
                time.sleep(0.003)

def main():
    file_path = input("Enter path to BMP (or any file) to send: ").strip()
    if not os.path.isfile(file_path):
        print("File not found.")
        return

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 8 * 1024 * 1024)  # bigger buffer
    try:
        rdt_send(sock, (SERVER_HOST, SERVER_PORT), file_path)
        print("[CLIENT] Done.")
    finally:
        sock.close()

if __name__ == "__main__":
    main()
