import socket
import struct
import time
import threading
import random
import sys

PACKET_SIZE = 1024
WINDOW_SIZE = 10
TIMEOUT = 0.2

LOSS_ACK = 0.0
ERROR_ACK = 0.0

def checksum(data: bytes) -> int:
    s = 0
    for i in range(0,len(data),2):
        if i +1 < len(data):
            w = (data[i] << 8) + data[i+1]
        else:
            w = (data[i] << 8)
        s = (s+w) & 0xFFFF
    return (~s) & 0xFFFF

def make_pkt(seq, payload):
    header = struct.pack("!IHH", seq, 0, len(payload))
    checks = checksum(header + payload)
    header = struct.pack("!IHH", seq, checks, len(payload))
    return header + payload

def parse_ack(data):
    if len(data) < 6:
        return None
    seq, checks = struct.unpack("!IH", data[:6])
    fake_head = struct.pack ("!IH", seq, 0)
    calculate = checksum(fake_head)

    if calculate != checks:
        return None
    return seq
class GBNSender:
    def __init__(self, udpfile, ip, port):
        self.destination = (ip, port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(0.05)

        with open(udpfile, "rb") as f:
            file = f.read()
        self.packets = []
        idx = 0
        seq = 0
        while idx < len(file):
            chunk = file[idx:idx+PACKET_SIZE]
            self.packets.append(make_pkt(seq, chunk))
            seq += 1
            idx += PACKET_SIZE

        self.base = 0
        self.nextseq = 0

        self.timer = None
        self.timer_start = 0

    def start_timer(self):
        self.timer_start = time.time()

    def timer_expired(self):
        return(time.time() - self.timer_start) > TIMEOUT

    def send(self):
        print(f"Total packets: {len(self.packets)}")
        while self.base < len(self.packets):
            while self.nextseq < min(self.base + WINDOW_SIZE, len(self.packets)):
              print(f"[SEND] PACKET {self.nextseq}")
              self.socket.sendto(self.packets[self.nextseq], self.destination)

              if self.base == self.nextseq:
                  self.start_timer()
              self.nextseq += 1

            try:
                data, _= self.socket.recvfrom(PACKET_SIZE)
                if random.random() < LOSS_ACK:
                    print("[SIM] Dropped ACK")
                    continue
                if random.random() <ERROR_ACK:
                    data = bytearray(data)
                    data[3] ^= 0xFF
                    data = bytes(data)

                ack = parse_ack(data)
                if ack is not None:
                    print(f"[ACK] Received ACK {ack}")
                    self.base = ack + 1

                    if self.base == self.nextseq:
                        pass
                    else:
                        self.start_timer()
            except socket.timeout:
                pass
            if self.base != self.nextseq and self.timer_expired():
                print("[TIMEOUT] Resending window")
                for i in range(self.base, self.nextseq):
                    print(f"[RESEND] Packet {i}")
                    self.socket.sendto(self.packets[i], self.destination)
                self.start_timer()
        print("File transfer complete.")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python client.py <file> <server_ip> <server_port>")
        exit()

    sender = GBNSender(sys.argv[1], sys.argv[2], int(sys.argv[3]))
    sender.send()
    start = time.time()
    sender.send()
    end = time.time()
    print("Completion time:", end - start)









