import socket, time, struct, random, argparse, sys

TYPE_DATA = 0x01
TYPE_ACK  = 0x02

def parse_pkt(raw):
    # read packet now
    try:
        t = raw[0]; seq = raw[1]
        if t == TYPE_DATA:
            ln = struct.unpack("!H", raw[2:4])[0]
            return {"ok": True, "type": t, "seq": seq, "len": ln, "payload": raw[4:4+ln]}
        if t == TYPE_ACK:
            return {"ok": True, "type": t, "seq": seq, "len": 0, "payload": b""}
    except:
        pass
    return {"ok": False, "len": 0}

def make_ack(seq):
    # build ack packet
    return struct.pack("!BB", TYPE_ACK, seq)

def make_data(seq, payload):
    # build data
    return struct.pack("!BBH", TYPE_DATA, seq, len(payload)) + payload

def drop(p):
    # maybe drop now
    return random.random() < p

def corrupt(b, p, skip=0):
    # flip one byte
    if random.random() < p and len(b) > skip:
        i = random.randint(skip, len(b)-1)
        return b[:i] + bytes([b[i] ^ 1]) + b[i+1:]
    return b

p = argparse.ArgumentParser()
p.add_argument("port", type=int, default=12007)
p.add_argument("outfile", default="udpfile_received.jpg")
p.add_argument("mode", type=int, default=1)
p.add_argument("rate", type=float, default=0.0)
p.add_argument("delay-ack-ms", type=float, default=0.0)
p.add_argument("file", default="udpfile.jpg")  # add file here
A = p.parse_args()

# set channel probs
DATA_FLIP = A.rate if A.mode == 3 else 0.0
DATA_LOSS = A.rate if A.mode == 5 else 0.0
ACK_FLIP  = A.rate if A.mode == 2 else 0.0
ACK_LOSS  = A.rate if A.mode == 4 else 0.0

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(("0.0.0.0", A.port))

expected = 0
dup_acks = 0
dropped_data = 0
acks_sent = 0
acks_dropped = 0
acks_corrupted = 0
total_bytes = 0
t0 = time.perf_counter()

# read data now
data_list = []
with open(A.file, "rb") as f2:
    while True:
        c = f2.read(1024)
        if not c: break
        data_list.append(c)

index = 0

with open(A.outfile, "wb") as f:
    while True:
        # get packet
        raw, addr = s.recvfrom(2048)

        if A.mode == 6:
            # receiver driven
            req = parse_pkt(raw)
            if not req["ok"]: continue
            if req["type"] == TYPE_ACK:
                if index >= len(data_list):
                    pkt = make_data(expected, b"")
                    s.sendto(pkt, addr)
                    break
                pkt = make_data(expected, data_list[index])
                s.sendto(pkt, addr)
                index += 1
                expected ^= 1
            continue

        # simulate data path
        if A.mode in (3,5):
            if drop(DATA_LOSS):
                dropped_data += 1
                continue
            raw = corrupt(raw, DATA_FLIP, skip=4)

        pkt = parse_pkt(raw)
        if pkt["ok"] and pkt["type"] == TYPE_DATA:
            if pkt["seq"] == expected:
                if pkt["len"] > 0:
                    f.write(pkt["payload"]); total_bytes += pkt["len"]
                ack = make_ack(expected); expected ^= 1
            else:
                dup_acks += 1; ack = make_ack(expected ^ 1)

            send_it = True
            if A.mode in (2,4):
                if drop(ACK_LOSS):
                    acks_dropped += 1; send_it = False
                else:
                    new_ack = corrupt(ack, ACK_FLIP)
                    if new_ack != ack: acks_corrupted += 1
                    ack = new_ack

            if send_it:
                s.sendto(ack, addr); acks_sent += 1

        if A.delay_ack_ms > 0:
            time.sleep(A.delay_ack_ms/1000.0)

        if pkt["ok"] and pkt["type"] == TYPE_DATA and pkt["len"] == 0:
            break

elapsed = time.perf_counter() - t0
print(f"WROTE_BYTES: {total_bytes}")
print(f"TOTAL_TIME_SEC: {elapsed:.6f}")
print(f"DUPLICATE_ACKS: {dup_acks}")
print(f"DROPPED_DATA: {dropped_data}")
print(f"ACKS_SENT: {acks_sent}")
print(f"ACKS_DROPPED: {acks_dropped}")
print(f"ACKS_CORRUPTED: {acks_corrupted}")
sys.stdout.flush()
