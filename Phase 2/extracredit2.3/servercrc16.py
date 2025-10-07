from socket import *
import struct, random, time

#   setup
serverPort = 12007
buffer = 1024
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(('', serverPort))  # listen for client

# for option 1 no bit errors
DATA_FLIP_PROB = 0.0 # use it for option 3, change it to .05

# ---------- tiny RDT2.2 header + checksum ----------
TYPE_DATA, TYPE_ACK, FLAG_FIN = 1, 2, 0x01
HDR_FMT = "!BBBBHH"
HDR_LEN = struct.calcsize(HDR_FMT)

# add two 16-bit numbers
def _add16(a, b):
    s = a + b
    return (s & 0xFFFF) + (s >> 16)
'''
# compute  16-bit checksum
def checksum16(b: bytes) -> int:
    if len(b) & 1:
        b += b'\x00'
    s = 0
    for i in range(0, len(b), 2):
       s = _add16(s, (b[i] << 8) | b[i+1])
    return (~s) & 0xFFFF
'''
def compute_crc16(data: bytes, poly=0x8005, init_val=0x0000) -> int:
    crc = init_val
    for byte in data:
        crc ^= (byte << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ poly) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


# build the 8-byte header
def _hdr(t, seq, fl, ln, cs):
    return struct.pack(HDR_FMT, t & 0xFF, seq & 0xFF, fl & 0xFF, 0, ln & 0xFFFF, cs & 0xFFFF)

# make an ACK packet
def make_ack(seq: int) -> bytes:
    h0 = _hdr(TYPE_ACK, seq, 0, 0, 0)
   # return _hdr(TYPE_ACK, seq, 0, 0, checksum16(h0))
    cs = compute_crc16(h0)
    return _hdr(TYPE_ACK, seq, 0, 0, cs)


# analyze the  packet and verify CRC
def parse_pkt(raw: bytes):
    if len(raw) < HDR_LEN:
        return {"ok": False}
    t, seq, fl, _, ln, cs = struct.unpack(HDR_FMT, raw[:HDR_LEN])
    pl = raw[HDR_LEN:HDR_LEN+ln]
    if len(pl) != ln:
        return {"ok": False}
    #ok = checksum16(_hdr(t, seq, fl, ln, 0) + pl) == cs
    ok = compute_crc16(_hdr(t, seq, fl, ln, 0) + pl) == cs
    return {"ok": ok, "type": t, "seq": seq, "flags": fl, "length": ln, "payload": pl}

# flip exactly one random bit
def flip1(b: bytes) -> bytes:
    if not b:
        return b
    bb = bytearray(b)
    i = random.randrange(len(bb))
    bb[i] ^= 1 << random.randrange(8)
    return bytes(bb)

# maybe corrupt the received bytes
def maybe_corrupt(b: bytes, p: float) -> bytes:
   # p = max(0.0, min(1.0, float(p))) use it for option three
    return flip1(b) if (p > 0 and random.random() < min(max(p, 0.0), 1.0)) else b

#  first message: total size
first, clientAddress = serverSocket.recvfrom(2048)
remove = int(first.decode().strip())

# write received bytes to this output file
outfile = "udpfile_received.jpg"
fout = open(outfile, 'wb')

expected_seq = 0     # we want DATA with seq=0
last_good_seq = 1    # used for re-ACK
written = 0
t0 = None

#  receive reliably
while remove > 0:
    raw, _ = serverSocket.recvfrom(HDR_LEN + buffer + 512)
    raw = maybe_corrupt(raw, DATA_FLIP_PROB)
    pkt = parse_pkt(raw)
    if t0 is None:
        t0 = time.perf_counter()

    # bad/corrupt/not DATA
    if (not pkt.get("ok")) or pkt.get("type") != TYPE_DATA:
        serverSocket.sendto(make_ack(last_good_seq), clientAddress)
        continue

    seq = pkt["seq"]
    if seq == expected_seq:
        if pkt["length"] > 0:
            fout.write(pkt["payload"])
            written += pkt["length"]
            remove  -= pkt["length"]
        serverSocket.sendto(make_ack(seq), clientAddress)
        last_good_seq = seq
        expected_seq ^= 1
    else:
        # duplicate
        serverSocket.sendto(make_ack(last_good_seq), clientAddress)


fout.close()
serverSocket.sendto(b"ok ", clientAddress)
print(f"Wrote: {outfile} ({written} bytes)")
print(f"TOTAL_TIME_SEC: {0.0 if t0 is None else time.perf_counter()-t0:.6f}")
serverSocket.close()