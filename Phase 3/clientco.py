import sys, socket, time, random, argparse
from socket import SHUT_RDWR, timeout
from threading import Thread, Event
import struct

# RDT constants
TYPE_DATA = 0x01
TYPE_ACK  = 0x02
PAYLOAD_SIZE = 1024

# Impairment globals 
ACK_FLIP_PROB = 0.0
ACK_LOSS_PROB = 0.0

def make_pkt(seq, payload):
    return struct.pack("!BBH", TYPE_DATA, seq, len(payload)) + payload

def make_ack(seq):
    return struct.pack("!BB", TYPE_ACK, seq)

def parse_pkt(raw):
    try:
        t = raw[0]
        seq = raw[1]
        if t == TYPE_ACK:
            return {"ok": True, "type": TYPE_ACK, "seq": seq}
        elif t == TYPE_DATA:
            length = struct.unpack("!H", raw[2:4])[0]
            return {"ok": True, "type": TYPE_DATA, "seq": seq, "len": length, "payload": raw[4:4+length]}
    except:
        pass
    return {"ok": False}

def maybe_corrupt(b, prob):
    if random.random() < prob and len(b) > 2:
        i = random.randint(2, len(b)-1)
        return b[:i] + bytes([b[i] ^ 0x01]) + b[i+1:]
    return b

def maybe_drop(prob):
    return random.random() < prob

# Globals for ack listener
_ack_for_seq = -1
_ack_event = Event()
_stop_event = Event()
_listener_thread = None

def _ack_listener():
    global _ack_for_seq
    try:
        while not _stop_event.is_set():
            try:
                raw, _ = clientSocket.recvfrom(2048)
            except timeout:
                continue
            except OSError:
                break

            if maybe_drop(ACK_LOSS_PROB):
                continue

            raw = maybe_corrupt(raw, ACK_FLIP_PROB)
            ack = parse_pkt(raw)

            if ack.get("ok") and ack.get("type") == TYPE_ACK:
                _ack_for_seq = ack.get("seq", -1)
                _ack_event.set()
    except:
        pass

# main sending loop 
parser = argparse.ArgumentParser()
parser.add_argument("--server", default="127.0.0.1")
parser.add_argument("--port", type=int, default=12007)
parser.add_argument("--file", default="udpfile.jpg")
parser.add_argument("--mode", type=int, default=1)
parser.add_argument("--rate", type=float, default=0.0)
parser.add_argument("--rto", type=float, default=0.04)
parser.add_argument("--delay-data-ms", type=float, default=0.0)
args = parser.parse_args()

# Set impairment
if args.mode == 2: ACK_FLIP_PROB = args.rate     # ACK bit-errors
if args.mode == 4: ACK_LOSS_PROB = args.rate     # ACK loss

clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
clientSocket.settimeout(0.01)

_listener_thread = Thread(target=_ack_listener, daemon=True)
_listener_thread.start()

seq = 0
retransmissions = 0
t0 = time.perf_counter()

with open(args.file, "rb") as f:
    while True:
        payload = f.read(PAYLOAD_SIZE)
        if not payload:
            break

        pkt = make_pkt(seq, payload)
        while True:
            clientSocket.sendto(pkt, (args.server, args.port))
            send_time = time.perf_counter()
            _ack_event.clear()

            while True:
                if _ack_event.wait(timeout=args.rto):
                    if _ack_for_seq == seq:
                        break
                if time.perf_counter() - send_time >= args.rto:
                    retransmissions += 1
                    break

            if _ack_for_seq == seq:
                break

        seq ^= 1
        if args.delay_data_ms > 0:
            time.sleep(args.delay_data_ms / 1000.0)

#cleanup
_stop_event.set()
time.sleep(0.05)
try: clientSocket.shutdown(SHUT_RDWR)
except: pass
try: clientSocket.close()
except: pass
try: _listener_thread.join(timeout=0.2)
except: pass

elapsed = time.perf_counter() - t0
print(f"TOTAL_TIME_SEC: {elapsed:.6f}")
print(f"RETRANSMISSIONS: {retransmissions}")
sys.stdout.flush()
