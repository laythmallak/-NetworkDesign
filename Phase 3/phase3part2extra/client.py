import socket, time, struct, random, argparse, sys, csv, os

TYPE_DATA = 0x01
TYPE_ACK  = 0x02
PAYLOAD_SIZE = 1024

def make_pkt(seq, payload):
    # make data
    return struct.pack("!BBH", TYPE_DATA, seq, len(payload)) + payload

def parse_pkt(raw):
    # read pkt
    try:
        t = raw[0]; seq = raw[1]
        if t == TYPE_ACK:
            return {"ok": True, "type": t, "seq": seq}
        if t == TYPE_DATA:
            ln = struct.unpack("!H", raw[2:4])[0]
            return {"ok": True, "type": t, "seq": seq, "len": ln, "payload": raw[4:4+ln]}
    except:
        pass
    return {"ok": False}

def drop(p):
    # maybe drop
    return random.random() < p

def corrupt(b, p, skip=0):
    # flip byte
    if random.random() < p and len(b) > skip:
        i = random.randint(skip, len(b)-1)
        return b[:i] + bytes([b[i] ^ 1]) + b[i+1:]
    return b

p = argparse.ArgumentParser()
p.add_argument("server", default="127.0.0.1")
p.add_argument("port", type=int, default=12007)
p.add_argument("file", default="udpfile.jpg")
p.add_argument("mode", type=int, default=1)
p.add_argument("rate", type=float, default=0.0)
p.add_argument("rto", type=float, default=0.04)
p.add_argument("delay-data-ms", type=float, default=0.0)
p.add_argument("csv", default="")
A = p.parse_args()

ACK_FLIP  = A.rate if A.mode == 2 else 0.0
ACK_LOSS  = A.rate if A.mode == 4 else 0.0
DATA_FLIP = A.rate if A.mode == 3 else 0.0
DATA_LOSS = A.rate if A.mode == 5 else 0.0

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.settimeout(A.rto)

seq = 0
retrans = 0
timeouts = 0
bytes_ok = 0
acks_total = 0
acks_useful = 0
t0 = time.perf_counter()

def send_with_problems(pkt):
    # data bugs
    if A.mode in (3,5):
        if drop(DATA_LOSS): return
        pkt = corrupt(pkt, DATA_FLIP, skip=4)
    s.sendto(pkt, (A.server, A.port))

def recv_ack_with_problems():
    # ack bugs
    try:
        raw, _ = s.recvfrom(2048)
    except socket.timeout:
        return {"ok": False}
    if drop(ACK_LOSS): return {"ok": False}
    raw = corrupt(raw, ACK_FLIP)
    ack = parse_pkt(raw)
    if ack["ok"] and ack["type"] == TYPE_ACK:
        return ack
    return {"ok": False}

def make_request(seq):
    # ask data
    return struct.pack("!BBH", TYPE_ACK, seq, 0)

with open(A.file, "rb") as f:
    data_list = []
    while True:
        c = f.read(PAYLOAD_SIZE)
        if not c: break
        data_list.append(c)

if A.mode == 6:
    # receiver driven
    seq = 0
    t0 = time.perf_counter()
    while True:
        req = make_request(seq)
        s.sendto(req, (A.server, A.port))
        try:
            raw,_ = s.recvfrom(2048)
        except socket.timeout:
            # ask again
            continue
        pkt = parse_pkt(raw)
        if not pkt["ok"] or pkt["type"] != TYPE_DATA:
            # ignore bad
            continue
        if pkt["len"] == 0:
            # done now
            break
        # count bytes
        bytes_ok += pkt["len"]
        # say ok
        ack = make_request(pkt["seq"])
        s.sendto(ack,(A.server,A.port))
        # flip bit
        seq ^= 1
    elapsed = time.perf_counter() - t0
    kbps=(bytes_ok*8)/1000.0/elapsed if elapsed>0 else 0.0
    print("BYTES_OK:", bytes_ok)
    print("TOTAL_TIME_SEC:", round(elapsed,6))
    print("THROUGHPUT_KBPS:", round(kbps,2))
    sys.stdout.flush()
    if A.csv:
        new = not os.path.exists(A.csv)
        with open(A.csv, "a", newline="") as f:
            w = csv.writer(f)
            if new:
                w.writerow(["mode","rate","rto","payload_size",
                            "bytes_ok","total_time_s","kbps",
                            "retransmissions","timeouts",
                            "acks_total","acks_useful","ack_efficiency"])
            w.writerow([A.mode,A.rate,A.rto,1024,
                        bytes_ok,round(elapsed,4),round(kbps,2),
                        retrans,timeouts,acks_total,acks_useful,0.0])
    sys.exit(0)

with open(A.file, "rb") as f:
    while True:
        data = f.read(PAYLOAD_SIZE)
        last = (len(data) == 0)
        pkt = make_pkt(seq, b"" if last else data)

        while True:
            send_with_problems(pkt)
            start = time.perf_counter()
            good = False
            while True:
                ack = recv_ack_with_problems()
                if ack["ok"]:
                    acks_total += 1
                    if ack["seq"] == seq:
                        acks_useful += 1
                        good = True
                        break
                if time.perf_counter() - start >= A.rto:
                    retrans += 1; timeouts += 1
                    break
            if good: break

        if last: break
        bytes_ok += len(data)
        seq ^= 1
        if A.delay_data_ms > 0:
            time.sleep(A.delay_data_ms/1000.0)

elapsed = time.perf_counter() - t0
kbps = (bytes_ok*8)/1000.0/elapsed if elapsed>0 else 0.0
eff = (acks_useful/acks_total) if acks_total else 0.0

print("BYTES_OK:", bytes_ok)
print("TOTAL_TIME_SEC:", round(elapsed,6))
print("THROUGHPUT_KBPS:", round(kbps,2))
print("RETRANSMISSIONS:", retrans)
print("TIMEOUTS:", timeouts)
print("ACKS_TOTAL:", acks_total)
print("ACKS_USEFUL:", acks_useful)
print("ACK_EFFICIENCY:", round(eff,3))
sys.stdout.flush()

if A.csv:
    new = not os.path.exists(A.csv)
    with open(A.csv, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["mode","rate","rto","payload_size",
                        "bytes_ok","total_time_s","kbps",
                        "retransmissions","timeouts",
                        "acks_total","acks_useful","ack_efficiency"])
        w.writerow([A.mode,A.rate,A.rto,1024,
                    bytes_ok,round(elapsed,4),round(kbps,2),
                    retrans,timeouts,acks_total,acks_useful,round(eff,4)])