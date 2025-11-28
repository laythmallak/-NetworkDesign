import sys
import socket
import struct
import time
import os

MSS = 1000  # bytes per packet

# header
HDR_FMT = "!I H H"
HDR_SIZE = struct.calcsize(HDR_FMT)


def checksum(b: bytes) -> int:
    # small checksum
    return sum(b) & 0xFFFF


def make_pkt(seq: int, data: bytes) -> bytes:
    length = len(data)
    header = struct.pack(HDR_FMT, seq, length, 0)
    cs = checksum(header + data)
    header = struct.pack(HDR_FMT, seq, length, cs)
    return header + data


def parse_pkt(pkt: bytes):
    # check size
    if len(pkt) < HDR_SIZE:
        return None
    header = pkt[:HDR_SIZE]
    seq, length, cs = struct.unpack(HDR_FMT, header)
    data = pkt[HDR_SIZE:HDR_SIZE + length]
    # recompute checksum
    header0 = struct.pack(HDR_FMT, seq, length, 0)
    if checksum(header0 + data) != cs:
        return None
    return seq, data


def client_sw(ip: str, port: int, fname: str):
    # read file
    with open(fname, "rb") as f:
        data = f.read()

    # split into chunks
    chunks = []
    seq = 0
    i = 0
    while i < len(data):
        chunks.append((seq, data[i:i + MSS]))
        seq += 1
        i += MSS

    n = len(chunks)
    print(f"[SW CLIENT] total packets {n}")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(0.5)
    addr = (ip, port)

    start_time = time.time()  # start time

    for idx in range(n):
        seq_id, d = chunks[idx]
        pkt = make_pkt(seq_id, d)

        # send until we get ACK
        while True:
            sock.sendto(pkt, addr)
            print(f"[SW CLIENT] Sent packet {seq_id}")
            try:
                ack_pkt, _ = sock.recvfrom(1024)
                if len(ack_pkt) == 4:
                    (ack_seq,) = struct.unpack("!I", ack_pkt)
                    print(f"[SW CLIENT] Got ACK {ack_seq}")
                    if ack_seq == seq_id:
                        break  # go to next packet
            except socket.timeout:
                # no ACK, resend
                print(f"[SW CLIENT] Timeout on {seq_id}, resend")

    # send END
    sock.sendto(b"END", addr)
    end_time = time.time()
    duration = end_time - start_time
    print(f"[SW CLIENT] Done. Time = {duration:.3f} seconds")

    sock.close()


def server_sw(port: int):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", port))
    print(f"[SW SERVER] Listening on port {port}, writing to udpfile_received.jpg")

    expected = 0
    client = None
    f = open("udpfile_received.jpg", "wb")

    while True:
        pkt, addr = sock.recvfrom(4096)
        if pkt == b"END":
            print("[SW SERVER] END received, closing.")
            break

        if client is None:
            client = addr

        p = parse_pkt(pkt)
        if p is None:
            # bad packet, ignore
            continue

        seq, data = p

        if seq == expected:
            # in order: write and move to next
            f.write(data)
            print(f"[SW SERVER] Got packet {seq}")
            expected += 1

        # send ACK for last correct packet
        ack_seq = expected - 1
        if ack_seq < 0:
            ack_seq = 0
        ack = struct.pack("!I", ack_seq)
        sock.sendto(ack, client)

    f.close()
    sock.close()
    print("[SW SERVER] Done.")


def main():
    if len(sys.argv) < 3:
        print("Usage:")
        print("  server: py -3 stopAwait.py server <port>")
        print("  client: py -3 stopAwait.py client <server_ip> <port> <filename>")
        sys.exit(1)

    mode = sys.argv[1]
    if mode == "server":
        port = int(sys.argv[2])
        server_sw(port)
    elif mode == "client":
        if len(sys.argv) < 5:
            print("client: py -3 stopAwait.py client <server_ip> <port> <filename>")
            sys.exit(1)
        ip = sys.argv[2]
        port = int(sys.argv[3])
        fname = sys.argv[4]
        if not os.path.exists(fname):
            print("file not found:", fname)
            sys.exit(1)
        client_sw(ip, port, fname)
    else:
        print("mode must be server or client")
        sys.exit(1)


if __name__ == "__main__":
    main()