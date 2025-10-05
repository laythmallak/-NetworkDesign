from socket import *
import os, struct, random, time
import threading

#  setup
serverName = "127.0.0.1"       # the server ip address
serverPort = 12007             # server port number
buffer = 1024                  # bytes per data
clientSocket = socket(AF_INET, SOCK_DGRAM) # socket is being created

clientSocket.settimeout(10)    # avoid waiting for long time
file = "udpfile.jpg"           #  file to send

# no bit errors
ACK_FLIP_PROB = 0.00  # for option two,  it will be .05

DELAY_DATA_MAX_MS = 500

RTO = 0.5

# tiny RDT2.2 header + checksum
TYPE_DATA, TYPE_ACK, FLAG_FIN = 1, 2, 0x01
HDR_FMT = "!BBBBHH"
HDR_LEN = struct.calcsize(HDR_FMT)

# add two 16-bit numbers
def _add16(a, b):
    s = a + b
    return (s & 0xFFFF) + (s >> 16)

# compute  16-bit checksum to catch the bit errors
def checksum16(b: bytes) -> int:
    if len(b) & 1:
        b += b'\x00'
    s = 0
    for i in range(0, len(b), 2):
        s = _add16(s, (b[i] << 8) | b[i+1])
    return (~s) & 0xFFFF

# build the 8-byte header
def _hdr(t, seq, fl, ln, cs):
    return struct.pack(HDR_FMT, t & 0xFF, seq & 0xFF, fl & 0xFF, 0, ln & 0xFFFF, cs & 0xFFFF)

# make one DATA packet header+payload with  checksum
def make_data(seq: int, payload: bytes, fin: bool = False) -> bytes:
    fl = FLAG_FIN if fin else 0
    h0 = _hdr(TYPE_DATA, seq, fl, len(payload), 0)
    cs = checksum16(h0 + payload)
    return _hdr(TYPE_DATA, seq, fl, len(payload), cs) + payload

# it will check the checksum for errors and return the fields
def parse_pkt(raw: bytes):
    if len(raw) < HDR_LEN:
        return {"ok": False}
    t, seq, fl, _, ln, cs = struct.unpack(HDR_FMT, raw[:HDR_LEN])
    pl = raw[HDR_LEN:HDR_LEN+ln]
    if len(pl) != ln:
        return {"ok": False}
    ok = checksum16(_hdr(t, seq, fl, ln, 0) + pl) == cs
    return {"ok": ok, "type": t, "seq": seq, "flags": fl, "length": ln, "payload": pl}

# flip exactly one random bit
def flip1(b: bytes) -> bytes:
    if not b:
        return b
    bb = bytearray(b)
    i = random.randrange(len(bb))
    bb[i] ^= 1 << random.randrange(8)
    return bytes(bb)

# corrupt one byte by flipping onre bit
def maybe_corrupt(b: bytes, p: float) -> bytes:
    #p = max(0.0, min(1.0, float(p))) use for option 2
    return flip1(b) if (p > 0 and random.random() < min(max(p, 0.0), 1.0)) else b

#  send size first so server knows how much to expect
filesize = os.path.getsize(file)
clientSocket.sendto(str(filesize).encode("utf-8"), (serverName, serverPort))

_ack_for_seq = -1
_ack_event = threading.Event()
_stop_event = threading.Event()

def _ack_listener(): 
    #reads socket, calidates ACK, signals sender loop
    global _ack_for_seq
    while not _stop_event.is_set():
        try:
            raw, _ = clientSocket.recvfrom(2048)
        except timeout:
            continue
        raw = maybe_corrupt(raw, ACK_FLIP_PROB)
        ack = parse_pkt(raw)
        if ack.get("ok") and ack.get("type") == TYPE_ACK:
            global _ack_for_seq
            _ack_for_seq = ack.get("seq", -1)
            _ack_event.set()

_listener_thread = threading.Thread(target=_ack_listener, daemon=True)
_listener_thread.start()

#  send file reliably
with open(file, "rb") as f:
    storing = 0           # bytes successfully ACKed
    seq = 0               # alternating bit
    t0 = time.perf_counter()
    retransmissions = 0

    while storing < filesize:
        chunk = f.read(buffer)
        if not chunk:
            break
        fin = (storing + len(chunk) >= filesize)
        pkt = make_data(seq, chunk, fin)

        # send this DATA until we get the correct ACK
        first_try = True
        while True:
            if DELAY_DATA_MAX_MS > 0:
                time.sleep(random.uniform(0, DELAY_DATA_MAX_MS) / 1000.0)
            _ack_event.clear()
            clientSocket.sendto(pkt, (serverName, serverPort))
            got = _ack_event.wait(timeout=RTO)
            
            if got and _ack_for_seq == seq:
                storing += len(chunk)
                seq ^= 1
                break
            else:
                if not first_try:
                    retransmissions += 1
                first_try = False

_stop_event.set()
try:
    msg, _ = clientSocket.recvfrom(2048)
    print(msg.decode())
except timeout:
    print("done")

print(f"TOTAL TIME: {time.perf_counter() - t0:.6f}")
print(f"RETRANSMISSIONS: {retransmissions}")
clientSocket.close()