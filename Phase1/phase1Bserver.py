# Phase 2: UDP file receiver (RDT 1.0 with buffer fix)
import os
import socket
import struct

SERVER_HOST = "0.0.0.0"
SERVER_PORT = 5051           # updated to avoid conflicts
MAX_PAYLOAD = 1024
BUF_SIZE    = 1500

# META: type(1)=0, file_size(4), total_pkts(4), name_len(2), name(name_len bytes)
META_HDR_FMT  = ">B I I H"
META_HDR_SIZE = struct.calcsize(META_HDR_FMT)

# DATA: type(1)=1, index(4), payload_len(2), payload(payload_len bytes)
DATA_HDR_FMT  = ">B I H"
DATA_HDR_SIZE = struct.calcsize(DATA_HDR_FMT)

TYPE_META = 0
TYPE_DATA = 1

def rdt_rcv(sock):
    return sock.recvfrom(BUF_SIZE)

def extract(pkt):
    ptype = pkt[0]
    if ptype == TYPE_META:
        _, fsize, tpkts, nlen = struct.unpack(META_HDR_FMT, pkt[:META_HDR_SIZE])
        fname = pkt[META_HDR_SIZE:META_HDR_SIZE+nlen].decode("utf-8", errors="ignore")
        return {"type": TYPE_META, "file_size": fsize, "total_pkts": tpkts, "file_name": fname}
    elif ptype == TYPE_DATA:
        _, index, plen = struct.unpack(DATA_HDR_FMT, pkt[:DATA_HDR_SIZE])
        payload = pkt[DATA_HDR_SIZE:DATA_HDR_SIZE+plen]
        return {"type": TYPE_DATA, "index": index, "payload": payload}
    else:
        raise ValueError("Unknown packet type")

def deliver_data(state, part):
    if part["type"] == TYPE_META:
        state["file_name"]  = part["file_name"]
        state["file_size"]  = part["file_size"]
        state["total_pkts"] = part["total_pkts"]
        state["buffer"]     = bytearray(state["file_size"])
        state["received"]   = 0
        state["seen"]       = set()
        print(f"[SERVER] Incoming file: {state['file_name']} "
              f"({state['file_size']} bytes) in {state['total_pkts']} packets")
        return

    if part["type"] == TYPE_DATA:
        idx, payload = part["index"], part["payload"]
        if idx not in state["seen"]:
            state["seen"].add(idx)
            offset = idx * MAX_PAYLOAD
            state["buffer"][offset:offset+len(payload)] = payload
            state["received"] += 1
            if state["received"] % 100 == 0 or state["received"] == state["total_pkts"]:
                print(f"[SERVER] Received {state['received']}/{state['total_pkts']}")
        if state["received"] == state["total_pkts"]:
            out_name = _unique_name(state["file_name"])
            with open(out_name, "wb") as f:
                f.write(state["buffer"])
            print(f"[SERVER] Saved: {out_name}")
            _reset_state(state)

def _unique_name(name: str) -> str:
    base, ext = os.path.splitext(name)
    candidate = name
    i = 1
    while os.path.exists(candidate):
        candidate = f"{base}({i}){ext}"
        i += 1
    return candidate

def _reset_state(state):
    state.update({
        "file_name": None, "file_size": None, "total_pkts": None,
        "buffer": None, "received": 0, "seen": set()
    })

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 8 * 1024 * 1024)  # bigger buffer
    sock.bind((SERVER_HOST, SERVER_PORT))
    print(f"[SERVER] UDP listening on {SERVER_HOST}:{SERVER_PORT}")

    state = {"file_name": None, "file_size": None, "total_pkts": None,
             "buffer": None, "received": 0, "seen": set()}

    while True:
        try:
            pkt, _ = rdt_rcv(sock)
            part   = extract(pkt)
            deliver_data(state, part)
        except Exception as e:
            print(f"[SERVER] Packet error: {e}")

if __name__ == "__main__":
    main()
