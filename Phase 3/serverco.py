import sys, socket, time, struct, random, argparse

TYPE_DATA = 0x01
TYPE_ACK  = 0x02

DATA_FLIP_PROB = 0.0
DATA_LOSS_PROB = 0.0

def parse_pkt(raw):
    try:
        t = raw[0]; seq = raw[1]
        if t == TYPE_DATA:
            length = struct.unpack("!H", raw[2:4])[0]
            return {"ok": True, "type": TYPE_DATA, "seq": seq, "len": length,
                    "payload": raw[4:4+length]}
    except:
        pass
    return {"ok": False}

def make_ack(seq):
    return struct.pack("!BB", TYPE_ACK, seq)

def maybe_corrupt(b):
    if random.random() < DATA_FLIP_PROB and len(b) > 4:
        i = random.randint(4, len(b)-1)
        return b[:i] + bytes([b[i] ^ 0x01]) + b[i+1:]
    return b

def maybe_drop():
    return random.random() < DATA_LOSS_PROB

parser = argparse.ArgumentParser()
parser.add_argument("--port", type=int, default=12007)
parser.add_argument("--outfile", default="udpfile_received.jpg")
parser.add_argument("--mode", type=int, default=1)
parser.add_argument("--rate", type=float, default=0.0)
parser.add_argument("--delay-ack-ms", type=float, default=0.0)
args = parser.parse_args()

if args.mode == 3: DATA_FLIP_PROB = args.rate
if args.mode == 5: DATA_LOSS_PROB = args.rate

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", args.port))

expected = 0
duplicate_acks = 0
dropped = 0
total_bytes = 0
t0 = time.perf_counter()

with open(args.outfile, "wb") as f:
    while True:
        try:
            raw, addr = sock.recvfrom(2048)
        except:
            break

        if args.mode in (3,5):
            if maybe_drop():
                dropped += 1
                continue
            raw = maybe_corrupt(raw)

        p = parse_pkt(raw)
        if p["ok"] and p["type"] == TYPE_DATA:
            seq = p["seq"]
            if seq == expected:
                f.write(p["payload"])
                total_bytes += p["len"]
                ack = make_ack(expected)
                expected ^= 1
            else:
                duplicate_acks += 1
                ack = make_ack(expected ^ 1)
            sock.sendto(ack, addr)

        elif p["ok"]:
            sock.sendto(make_ack(expected ^ 1), addr)

        if args.delay_ack_ms > 0:
            time.sleep(args.delay_ack_ms/1000.0)
        if p["ok"] and p["len"] == 0:
            break

elapsed = time.perf_counter() - t0
print(f"WROTE_BYTES: {total_bytes}")
print(f"TOTAL_TIME_SEC: {elapsed:.6f}")
print(f"DUPLICATE_ACKS: {duplicate_acks}")
print(f"DROPPED_DATA: {dropped}")
sys.stdout.flush()
