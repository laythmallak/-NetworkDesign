import sys
import socket
import struct
import time
import os
import threading

MSS = 1000      # bytes per packet
WIN = 10        # window size
TO  = 0.2       # timeout seconds

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
    data = pkt[HDR_SIZE:HDR_SIZE+length]
    header0 = struct.pack(HDR_FMT, seq, length, 0)
    if checksum(header0 + data) != cs:
        return None
    return seq, data

# GBN SERVER

def server_gbn(port: int):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", port))
    print(f"[GBN MT SERVER] Listening on port {port}, writing to udpfile_received_mt.jpg")

    exp_seq = 0
    client = None
    f = open("udpfile_received_mt.jpg", "wb")

    while True:
        pkt, addr = sock.recvfrom(4096)
        if pkt == b"END":
            print("[GBN MT SERVER] END received, closing.")
            break

        if client is None:
            client = addr

        p = parse_pkt(pkt)
        if p is None:
            # bad packet, send dup ack for last good
            ack = struct.pack("!I", exp_seq - 1)
            sock.sendto(ack, client)
            continue

        seq, data = p

        if seq == exp_seq:
            # in order
            f.write(data)
            print(f"[GBN MT SERVER] Got packet {seq}")
            ack = struct.pack("!I", seq)
            sock.sendto(ack, client)
            exp_seq += 1
        else:
            # out of order, send ack for last in order
            ack = struct.pack("!I", exp_seq - 1)
            sock.sendto(ack, client)

    f.close()
    sock.close()
    print("[GBN MT SERVER] Done.")

#  GBN CLIENT MULTI THREAD

def client_gbn_mt(ip: str, port: int, fname: str):
    # read file
    with open(fname, "rb") as f:
        data = f.read()

    # make chunks
    chunks = []
    seq = 0
    i = 0
    while i < len(data):
        chunks.append((seq, data[i:i+MSS]))
        seq += 1
        i += MSS

    n = len(chunks)
    print(f"[GBN MT CLIENT] total packets {n}")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(0.05)
    addr = (ip, port)

    # shared state
    lock = threading.Lock()
    base = 0
    next_seq = 0
    send_times = {}
    done = False
    stop_event = threading.Event()

    start_time = time.time()

    # sender thread
    def sender():
        nonlocal next_seq
        while not stop_event.is_set():
            with lock:
                # window not full and still packets left
                while next_seq < n and next_seq < base + WIN:
                    seq_id, d = chunks[next_seq]
                    pkt = make_pkt(seq_id, d)
                    sock.sendto(pkt, addr)
                    send_times[seq_id] = time.time()
                    print(f"[GBN MT CLIENT] Sent packet {seq_id}")
                    next_seq += 1
            time.sleep(0.001)

    # receiver thread (acks)
    def receiver():
        nonlocal base
        while not stop_event.is_set():
            try:
                pkt, _ = sock.recvfrom(1024)
            except socket.timeout:
                continue
            if len(pkt) == 4:
                (ack_seq,) = struct.unpack("!I", pkt)
                with lock:
                    if ack_seq + 1 > base:
                        base = ack_seq + 1
                        print(f"[GBN MT CLIENT] Got ACK {ack_seq}")
                        # if all done, stop event
                        if base >= n:
                            break
        # flag stop when exit
        stop_event.set()

    # timer thread
    def timer_thread():
        while not stop_event.is_set():
            time.sleep(0.01)
            with lock:
                if base >= n:
                    break
                now = time.time()
                # check oldest unacked
                if base in send_times and now - send_times[base] > TO:
                    print(f"[GBN MT CLIENT] Timeout at {base}, resend window")
                    # resend all in window
                    for s in range(base, min(base + WIN, n)):
                        seq_id, d = chunks[s]
                        pkt = make_pkt(seq_id, d)
                        sock.sendto(pkt, addr)
                        send_times[seq_id] = time.time()
                        print(f"[GBN MT CLIENT] Resent packet {seq_id}")
        stop_event.set()

    t_send = threading.Thread(target=sender, daemon=True)
    t_recv = threading.Thread(target=receiver, daemon=True)
    t_timer = threading.Thread(target=timer_thread, daemon=True)

    t_send.start()
    t_recv.start()
    t_timer.start()

    # wait until all acks
    while True:
        with lock:
            if base >= n:
                break
        time.sleep(0.01)

    stop_event.set()
    time.sleep(0.05)

    # send END
    sock.sendto(b"END", addr)
    sock.close()

    total_time = time.time() - start_time
    print(f"[GBN MT CLIENT] Done. Time = {total_time:.3f} seconds")

#  MAIN

def main():
    if len(sys.argv) < 3:
        print("Usage:")
        print("  server: py -3 GbackN_mt.py server <port>")
        print("  client: py -3 GbackN_mt.py client <server_ip> <port> <filename>")
        sys.exit(1)

    mode = sys.argv[1]
    if mode == "server":
        port = int(sys.argv[2])
        server_gbn(port)
    elif mode == "client":
        if len(sys.argv) < 5:
            print("client: py -3 GbackN_mt.py client <server_ip> <port> <filename>")
            sys.exit(1)
        ip = sys.argv[2]
        port = int(sys.argv[3])
        fname = sys.argv[4]
        if not os.path.exists(fname):
            print("file not found:", fname)
            sys.exit(1)
        client_gbn_mt(ip, port, fname)
    else:
        print("mode must be server or client")
        sys.exit(1)

if __name__ == "__main__":
    main()