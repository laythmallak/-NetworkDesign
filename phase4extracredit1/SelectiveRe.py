import sys
import socket
import struct
import time
import os


MSS = 1000          # bytes

WIN = 10            # window size

TO = 0.2         # timeout

# packet header
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


def client_sr(ip: str, port: int, fname: str):

    # read full file
    with open(fname, "rb") as f:
        data = f.read()

    # start timer
    start_time = time.time()

    # split file into chunks
    chunks = []
    seq = 0
    i = 0
    while i < len(data):
        chunks.append((seq, data[i:i + MSS]))
        seq += 1
        i += MSS

    n = len(chunks)
    print(f"[SR CLIENT] total packets {n}")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(0.05)
    addr = (ip, port)

    base = 0                 # first unacked packet index
    acked = [False] * n      # which packets are done
    sent_time = {}           # last send time per seq

    while base < n:
        now = time.time()

        # send or resend packets in window
        for s in range(base, min(base + WIN, n)):
            if acked[s]:
                continue
            if s not in sent_time or now - sent_time[s] > TO:
                seq_id, d = chunks[s]
                pkt = make_pkt(seq_id, d)
                sock.sendto(pkt, addr)
                sent_time[s] = now
                print(f"[SR CLIENT] Sent {s}")

        # receive ACKs 4 bytes seq number
        try:
            pkt, _ = sock.recvfrom(1024)
            if len(pkt) == 4:
                (ack_seq,) = struct.unpack("!I", pkt)
                if 0 <= ack_seq < n and not acked[ack_seq]:
                    acked[ack_seq] = True
                    print(f"[SR CLIENT] Got ACK {ack_seq}")
                    # move base to next not-acked
                    while base < n and acked[base]:
                        base += 1
        except socket.timeout:
            # no ACK, loop again and maybe resend
            pass

    # tell server we are done
    sock.sendto(b"END", addr)
    sock.close()

    # stop timer and print total time
    end_time = time.time()
    total = end_time - start_time
    print(f"[SR CLIENT] Done. Time = {total:.3f} seconds")


def server_sr(port: int):

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", port))
    print(f"[SR SERVER] Listening on port {port}, writing to udpfile_received.jpg")

    base = 0            # next seq we want in order
    buf = {}            # buffer for out-of-order data
    client = None
    f = open("udpfile_received.jpg", "wb")

    while True:
        pkt, addr = sock.recvfrom(4096)

        # end of file
        if pkt == b"END":
            print("[SR SERVER] END received, closing.")
            break

        if client is None:
            client = addr

        result = parse_pkt(pkt)
        if result is None:
            # bad packet, ignore
            continue

        seq, data = result

        # check if seq is inside window
        if base <= seq < base + WIN:
            if seq not in buf:
                buf[seq] = data
                print(f"[SR SERVER] Got packet {seq}")

            # ACK back the seq (4 bytes)
            ack = struct.pack("!I", seq)
            sock.sendto(ack, client)

            # write all in-order data
            while base in buf:
                f.write(buf[base])
                del buf[base]
                base += 1
        else:
            # packet outside window still ACK so sender can stop resending
            ack = struct.pack("!I", seq)
            sock.sendto(ack, addr)

    f.close()
    sock.close()
    print("[SR SERVER] Done.")


def main():
    if len(sys.argv) < 3:
        print("Usage:")
        print("  server: py -3 SelectiveRe.py server <port>")
        print("  client: py -3 SelectiveRe.py client <server_ip> <port> <filename>")
        sys.exit(1)

    mode = sys.argv[1]

    if mode == "server":
        port = int(sys.argv[2])
        server_sr(port)

    elif mode == "client":
        if len(sys.argv) < 5:
            print("client: py -3 SelectiveRe.py client <server_ip> <port> <filename>")
            sys.exit(1)
        ip = sys.argv[2]
        port = int(sys.argv[3])
        fname = sys.argv[4]
        if not os.path.exists(fname):
            print("file not found:", fname)
            sys.exit(1)
        client_sr(ip, port, fname)

    else:
        print("mode must be server or client")
        sys.exit(1)


if __name__ == "__main__":
    main()