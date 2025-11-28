import sys
import socket
import struct
import time
import os

MSS = 1000  # bytes per packet
WIN = 10    # window size
TO = 0.2    # timeout

# header
HDR_FMT = "!I H H"
HDR_SIZE = struct.calcsize(HDR_FMT)


def checksum(b: bytes) -> int:
    return sum(b) & 0xFFFF


def make_pkt(seq: int, data: bytes) -> bytes:
    length = len(data)
    header = struct.pack(HDR_FMT, seq, length, 0)
    cs = checksum(header + data)
    header = struct.pack(HDR_FMT, seq, length, cs)
    return header + data


def parse_pkt(pkt: bytes):
    if len(pkt) < HDR_SIZE:
        return None
    header = pkt[:HDR_SIZE]
    seq, length, cs = struct.unpack(HDR_FMT, header)
    data = pkt[HDR_SIZE:HDR_SIZE + length]
    header0 = struct.pack(HDR_FMT, seq, length, 0)
    if checksum(header0 + data) != cs:
        return None
    return seq, data


def client_gbn(ip: str, port: int, fname: str):
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
    print(f"[GBN CLIENT] total packets {n}")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(0.05)
    addr = (ip, port)

    base = 0          # first un-acked packet
    next_seq = 0      # next packet to send
    timer_start = None

    start_time = time.time()  # start time

    while base < n:
        # send packets in window
        while next_seq < base + WIN and next_seq < n:
            seq_id, d = chunks[next_seq]
            pkt = make_pkt(seq_id, d)
            sock.sendto(pkt, addr)
            print(f"[GBN CLIENT] Sent packet {seq_id}")
            if base == next_seq:
                timer_start = time.time()
            next_seq += 1

        # wait for ACK or timeout
        try:
            pkt, _ = sock.recvfrom(1024)
            if len(pkt) == 4:
                (ack_seq,) = struct.unpack("!I", pkt)
                print(f"[GBN CLIENT] Got ACK {ack_seq}")
                # move base
                if ack_seq + 1 > base:
                    base = ack_seq + 1
                    if base == next_seq:
                        timer_start = None
                    else:
                        timer_start = time.time()
        except socket.timeout:
            # check timeout
            if timer_start is not None and (time.time() - timer_start > TO):
                print("[GBN CLIENT] Timeout, resend window")
                # resend all from base
                for s in range(base, next_seq):
                    seq_id, d = chunks[s]
                    pkt = make_pkt(seq_id, d)
                    sock.sendto(pkt, addr)
                    print(f"[GBN CLIENT] Resent packet {seq_id}")
                timer_start = time.time()

    # send END
    sock.sendto(b"END", addr)
    end_time = time.time()
    duration = end_time - start_time
    print(f"[GBN CLIENT] Done. Time = {duration:.3f} seconds")

    sock.close()


def server_gbn(port: int):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", port))
    print(f"[GBN SERVER] Listening on port {port}, writing to udpfile_received.jpg")

    expected = 0   # next seq we want
    client = None
    f = open("udpfile_received.jpg", "wb")

    while True:
        pkt, addr = sock.recvfrom(4096)
        if pkt == b"END":
            print("[GBN SERVER] END received, closing.")
            break

        if client is None:
            client = addr

        p = parse_pkt(pkt)
        if p is None:
            # bad packet, send ACK for last good packet
            ack_seq = expected - 1
            if ack_seq < 0:
                ack_seq = 0
            ack = struct.pack("!I", ack_seq)
            sock.sendto(ack, client)
            continue

        seq, data = p

        if seq == expected:
            # correct packet
            f.write(data)
            print(f"[GBN SERVER] Got packet {seq}")
            expected += 1
        else:
            # wrong seq, ignore data
            print(f"[GBN SERVER] Out of order {seq}, expected {expected}")

        # always ACK last in-order packet
        ack_seq = expected - 1
        if ack_seq < 0:
            ack_seq = 0
        ack = struct.pack("!I", ack_seq)
        sock.sendto(ack, client)

    f.close()
    sock.close()
    print("[GBN SERVER] Done.")


def main():
    if len(sys.argv) < 3:
        print("Usage:")
        print("  server: py -3 GbackN.py server <port>")
        print("  client: py -3 GbackN.py client <server_ip> <port> <filename>")
        sys.exit(1)

    mode = sys.argv[1]
    if mode == "server":
        port = int(sys.argv[2])
        server_gbn(port)
    elif mode == "client":
        if len(sys.argv) < 5:
            print("client: py -3 GbackN.py client <server_ip> <port> <filename>")
            sys.exit(1)
        ip = sys.argv[2]
        port = int(sys.argv[3])
        fname = sys.argv[4]
        if not os.path.exists(fname):
            print("file not found:", fname)
            sys.exit(1)
        client_gbn(ip, port, fname)
    else:
        print("mode must be server or client")
        sys.exit(1)


if __name__ == "__main__":
    main()