from socket import *
import struct, random, time, argparse
import threading
from queue import Queue, Empty

# ----------------- CLI -----------------
ap = argparse.ArgumentParser(description="RDT3.0 Receiver (server)")
ap.add_argument("--port", type=int, default=12007)
ap.add_argument("--mode", type=int, choices=[1,3,5], default=1,
                help="1: baseline | 3: DATA bit-errors | 5: DATA loss")
ap.add_argument("--rate", type=float, default=0.0, help="probability in [0,1]")
ap.add_argument("--delay-ack-ms", type=float, default=0.0,
                help="max random per-ACK delay (ms) for experimentation")
ap.add_argument("--outfile", default="udpfile_received.jpg")
args = ap.parse_args()

serverPort = args.port
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(('', serverPort))

rate = max(0.0, min(1.0, float(args.rate)))
DELAY_ACK_MAX_MS = max(0.0, float(args.delay_ack_ms))

# ---- Option toggles at RECEIVER (server) ----
DATA_FLIP_PROB = rate if args.mode == 3 else 0.0  # Option 3: DATA bit-errors
DATA_LOSS_PROB = rate if args.mode == 5 else 0.0  # Option 5: DATA loss

# -------------- tiny RDT header --------------
TYPE_DATA, TYPE_ACK, FLAG_FIN = 1, 2, 0x01
HDR_FMT = "!BBBBHH"
HDR_LEN = struct.calcsize(HDR_FMT)

def _add16(a, b):
    s = a + b
    return (s & 0xFFFF) + (s >> 16)

def checksum16(b: bytes) -> int:
    if len(b) & 1:
        b += b'\x00'
    s = 0
    for i in range(0, len(b), 2):
        s = _add16(s, (b[i] << 8) | b[i+1])
    return (~s) & 0xFFFF

def _hdr(t, seq, fl, ln, cs):
    return struct.pack(HDR_FMT, t & 0xFF, seq & 0xFF, fl & 0xFF, 0, ln & 0xFFFF, cs & 0xFFFF)

def make_ack(seq: int) -> bytes:
    h0 = _hdr(TYPE_ACK, seq, 0, 0, 0)
    return _hdr(TYPE_ACK, seq, 0, 0, checksum16(h0))

def parse_pkt(raw: bytes):
    if len(raw) < HDR_LEN:
        return {"ok": False}
    t, seq, fl, _, ln, cs = struct.unpack(HDR_FMT, raw[:HDR_LEN])
    pl = raw[HDR_LEN:HDR_LEN+ln]
    if len(pl) != ln:
        return {"ok": False}
    ok = checksum16(_hdr(t, seq, fl, ln, 0) + pl) == cs
    return {"ok": ok, "type": t, "seq": seq, "flags": fl, "length": ln, "payload": pl}

def flip1(b: bytes) -> bytes:
    if not b:
        return b
    bb = bytearray(b)
    i = random.randrange(len(bb))
    bb[i] ^= 1 << random.randrange(8)
    return bytes(bb)

def maybe_corrupt(b: bytes, p: float) -> bytes:
    return flip1(b) if (p > 0 and random.random() < min(max(p,0.0),1.0)) else b

def maybe_drop(p: float) -> bool:
    return (p > 0 and random.random() < min(max(p,0.0),1.0))

# ------------- get size -------------
first, clientAddress = serverSocket.recvfrom(2048)
remaining = int(first.decode().strip())

fout = open(args.outfile, 'wb')
expected_seq = 0
last_good_seq = 1
written = 0
t0 = None

_ack_q = Queue()
_stop_ack = threading.Event()
dup_acks = 0
dropped_data = 0

def _ack_sender():
    while not _stop_ack.is_set():
        try:
            seq = _ack_q.get(timeout=0.1)
        except Empty:
            continue
        if DELAY_ACK_MAX_MS > 0:
            time.sleep(random.uniform(0, DELAY_ACK_MAX_MS) / 1000.0)
        serverSocket.sendto(make_ack(seq), clientAddress)
        _ack_q.task_done()

threading.Thread(target=_ack_sender, daemon=True).start()

# ------------- receive reliably (RDT 3.0 receiver) -------------
while remaining > 0:
    raw, _ = serverSocket.recvfrom(HDR_LEN + 1024 + 512)

    # Option 5: DATA loss — drop before parsing (no ACK => sender timeout)
    if maybe_drop(DATA_LOSS_PROB):
        dropped_data += 1
        continue

    # Option 3: DATA bit-errors — corrupt before parsing
    raw = maybe_corrupt(raw, DATA_FLIP_PROB)

    pkt = parse_pkt(raw)
    if t0 is None:
        t0 = time.perf_counter()

    # corrupt/bad/not DATA
    if (not pkt.get("ok")) or pkt.get("type") != TYPE_DATA:
        _ack_q.put(last_good_seq)   # re-ACK last good (ignore dup/new bad)
        dup_acks += 1
        continue

    seq = pkt["seq"]
    if seq == expected_seq:
        if pkt["length"] > 0:
            fout.write(pkt["payload"])
            written += pkt["length"]
            remaining -= pkt["length"]
        _ack_q.put(seq)             # ACK current
        last_good_seq = seq
        expected_seq ^= 1
    else:
        _ack_q.put(last_good_seq)   # duplicate, re-ACK
        dup_acks += 1

fout.close()
_stop_ack.set()
serverSocket.sendto(b"ok", clientAddress)

print(f"WROTE_BYTES: {written}")
print(f"TOTAL_TIME_SEC: {0.0 if t0 is None else time.perf_counter()-t0:.6f}")
print(f"DUPLICATE_ACKS: {dup_acks}")
print(f"DROPPED_DATA: {dropped_data}")
serverSocket.close()
