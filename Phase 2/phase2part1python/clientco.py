from socket import *
import os, struct, random, time, argparse
import threading

# ----------------- CLI -----------------
ap = argparse.ArgumentParser(description="RDT3.0 Sender (client)")
ap.add_argument("--server", default="127.0.0.1")
ap.add_argument("--port", type=int, default=12007)
ap.add_argument("--file", default="udpfile.jpg", help="≥500 KB file for Phase 3")
ap.add_argument("--mode", type=int, choices=[1,2,4], default=1,
                help="1: baseline | 2: ACK bit-errors | 4: ACK loss")
ap.add_argument("--rate", type=float, default=0.0, help="probability in [0,1]")
ap.add_argument("--rto", type=float, default=0.04, help="retransmission timeout (sec)")
ap.add_argument("--delay-data-ms", type=float, default=0.0,
                help="max random per-send delay (ms) for experimentation")
args = ap.parse_args()

serverName = args.server
serverPort = args.port
buffer = 1024
rate = max(0.0, min(1.0, float(args.rate)))
DELAY_DATA_MAX_MS = max(0.0, float(args.delay_data_ms))
RTO = max(0.001, float(args.rto))

# ---- Option toggles at SENDER (client) ----
ACK_FLIP_PROB = rate if args.mode == 2 else 0.0   # Option 2: ACK bit-errors
ACK_LOSS_PROB = rate if args.mode == 4 else 0.0   # Option 4: ACK loss

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

def make_data(seq: int, payload: bytes, fin: bool = False) -> bytes:
    fl = FLAG_FIN if fin else 0
    h0 = _hdr(TYPE_DATA, seq, fl, len(payload), 0)
    cs = checksum16(h0 + payload)
    return _hdr(TYPE_DATA, seq, fl, len(payload), cs) + payload

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

# -------------- socket & size --------------
clientSocket = socket(AF_INET, SOCK_DGRAM)
clientSocket.settimeout(10)

filesize = os.path.getsize(args.file)
clientSocket.sendto(str(filesize).encode("utf-8"), (serverName, serverPort))

_ack_for_seq = -1
_ack_event = threading.Event()
_stop_event = threading.Event()

def _ack_listener():
    global _ack_for_seq
    while not _stop_event.is_set():
        try:
            raw, _ = clientSocket.recvfrom(2048)_
