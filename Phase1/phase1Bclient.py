# Phase 1B: UDP file sender 
# This client reads a file, splits it into fixed-size packets, 
# and sends them to the server over UDP.

import os
import math
import time
import socket
import struct

# server details 
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5051

# size of each chunk of data to send
MAX_PAYLOAD = 1024

# META: type (1B), file_size (4B), total_pkts (4B), name_len (2B)
META_HDR_FMT = ">B I I H"
# DATA: type (1B), index (4B), payload_len (2B)
DATA_HDR_FMT = ">B I H"

# packet types
TYPE_META = 0
TYPE_DATA = 1


def make_pkt(ptype, **kw):
    """
    Build a packet of the given type.
    TYPE_META includes file info and name.
    TYPE_DATA includes index and payload bytes.
    """
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
    """
    send a UDP packet
    """
    sock.sendto(pkt, addr)


def rdt_send(sock, addr, file_path):
    """
    Send the file reliably over UDP in fixed-size packets.
      1) Send META packet describing file.
      2) Read file in 1024-byte chunks.
      3) Send each chunk as a DATA packet with an index.
      4) Print progress every 100 packets.
      5) Sleep slightly every 200 packets to avoid flooding.
    """
    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    total_pkts = math.ceil(file_size / MAX_PAYLOAD)

    # send META first so server can prepare
    meta = make_pkt(TYPE_META, file_name=file_name, file_size=file_size, total_pkts=total_pkts)
    udt_send(sock, addr, meta)
    print(f"[CLIENT] META sent: {file_name}, {file_size} bytes, {total_pkts} packets")

    sent = 0
    with open(file_path, "rb") as f:
        for index in range(total_pkts):
            # read next chunk of file
            payload = f.read(MAX_PAYLOAD)
            pkt = make_pkt(TYPE_DATA, index=index, payload=payload)
            udt_send(sock, addr, pkt)
            sent += 1

            # show progress every 100 packets
            if sent % 100 == 0 or sent == total_pkts:
                print(f"[CLIENT] Sent {sent}/{total_pkts}")

            # pacing: small delay every 200 packets
            if (index + 1) % 200 == 0:
                time.sleep(0.003)


def main():
    """
    Prompts user for file, makes a socket, and sends the file.
    """
    file_path = input("Enter path to BMP (or any file) to send: ").strip()
    if not os.path.isfile(file_path):
        print("File not found.")
        return

    # create UDP socket and enlarge buffer to reduce drops
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 8 * 1024 * 1024)

    try:
        rdt_send(sock, (SERVER_HOST, SERVER_PORT), file_path)
        print("[CLIENT] Done.")
    finally:
        sock.close()


if __name__ == "__main__":
    main()
