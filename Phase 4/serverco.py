import socket
import struct
import random

LOSS_DATA = 0.0
ERROR_DATA = 0.0

def checksum(data: bytes) -> int:
    s = 0
    for i in range(0, len(data), 2):
        if i + 1 < len(data):
            w = (data[i] << 8) + data[i+1]
        else:
            w = (data[i] << 8)
            s = (s+w) & 0xFFFF
    return (~s) & 0xFFFF

def parse_packet(packet):
    if len(packet) < 8:
        return None, None, None
    seq, checks, length = struct.unpack("!IHH", packet[:8])
    payload = packet[8:]

    if len(payload) != length:
        return None, None, None
    cmp_header = struct.pack("!IHH", seq, 0, length)

    if checksum(cmp_header +payload) != checks:
        return None, None, None
    return seq, length, payload
def ack_packet(seq):
    header = struct.pack("!IH", seq, 0)
    checks = checksum(header)
    return struct.pack("IH", seq, checks)

class GBNReceiver:
    def __init__(self, port, outfile):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(("0.0.0.0", port))
        self.expected = 0
        self.out = (outfile, "wb")

    def run(self):
        print("Receiver started")

        while True:
            packet, addr = self.socket.recvform(1500)
            if random.random() < LOSS_DATA:
                print("Dropped Data Packet")
                continue
            if random.random() < ERROR_DATA:
                print("Bit FLipped in Data")
                packet = bytearray(packet)
                packet[5] ^= 0xFF
                packet = bytes(packet)
            seq, length, payload = parse_packet(packet)

            if seq is None:
                print("Error: Bad Checksum")
                continue

            print("Received Packet %d" % seq)
            if seq == self.expected:
                self.out.write(payload)
                self.expected += 1
            ack = ack_packet(self.expected - 1)
            print(" Sending ACK {self.expected-1}")
            self.socket.sendto(ack, addr)

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python server.py <port> <outfile>")
        exit()

    r = GBNReceiver(int(sys.argv[1]), sys.argv[2])
    r.run()







