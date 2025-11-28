import tkinter as tk
import random
import time





class GBNGui:
    def __init__(self, root):
        self.root = root
        root.title("Go-Back-N FSM Demo")


        self.num_packets = 20       # total packets to send
        self.win_size = 5           # window size
        self.loss_prob = 0.2        # packet loss
        self.step_ms = 400          # time between steps

        # protocol state
        self.base = 0
        self.nextseq = 0
        self.acked = [False] * self.num_packets
        self.in_flight = set()     # packets sent but not acked
        self.timeouts = {}         # simple timer per base
        self.timeout_limit = 3.0   # timeout
        self.done = False

        # sender / receiver FSM state
        self.sender_state = "IDLE"
        self.receiver_state = "WAIT_FOR_PKT"

        # layout
        self.build_ui()

        # start sim
        self.start_time = time.time()
        self.root.after(self.step_ms, self.step)

    def build_ui(self):

        top = tk.Frame(self.root)
        top.pack(pady=5)

        self.lbl_sender = tk.Label(top, text="Sender: IDLE", font=("Arial", 12))
        self.lbl_sender.pack(side=tk.LEFT, padx=10)

        self.lbl_receiver = tk.Label(top, text="Receiver: WAIT_FOR_PKT", font=("Arial", 12))
        self.lbl_receiver.pack(side=tk.LEFT, padx=10)

        self.lbl_info = tk.Label(self.root, text="", font=("Arial", 11))
        self.lbl_info.pack(pady=5)

        # window info
        self.lbl_window = tk.Label(self.root, text="", font=("Arial", 11))
        self.lbl_window.pack(pady=5)

        # canvas for packets
        self.canvas = tk.Canvas(self.root, width=800, height=200, bg="white")
        self.canvas.pack(padx=10, pady=10)

        # make packet rectangles
        self.packet_items = []
        margin = 10
        spacing = 35
        x = margin
        y = 50
        for i in range(self.num_packets):
            rect = self.canvas.create_rectangle(x, y, x+25, y+25, fill="lightgray")
            text = self.canvas.create_text(x+12, y+35, text=str(i), font=("Arial", 8))
            self.packet_items.append((rect, text))
            x += spacing

        # bottom info
        self.lbl_status = tk.Label(self.root, text="", font=("Arial", 11))
        self.lbl_status.pack(pady=5)

    def set_sender_state(self, s):
        self.sender_state = s
        self.lbl_sender.config(text=f"Sender: {s}")

    def set_receiver_state(self, s):
        self.receiver_state = s
        self.lbl_receiver.config(text=f"Receiver: {s}")

    def color_packet(self, idx, color):
        rect, _ = self.packet_items[idx]
        self.canvas.itemconfig(rect, fill=color)

    def send_new_packets(self):
        # send new packets while window not full
        self.set_sender_state("SENDING")
        while self.nextseq < self.num_packets and self.nextseq < self.base + self.win_size:
            if self.acked[self.nextseq]:
                self.nextseq += 1
                continue
            # send packet
            self.in_flight.add(self.nextseq)
            self.color_packet(self.nextseq, "lightblue")  # sent, waiting ack
            if self.base == self.nextseq:
                # start timer for base
                self.timeouts["base"] = time.time()
            self.nextseq += 1

    def maybe_timeout(self):
        # check simple timeout on base
        if "base" in self.timeouts and self.base < self.nextseq:
            elapsed = time.time() - self.timeouts["base"]
            if elapsed > self.timeout_limit:
                # timeout, resend all from base
                self.set_sender_state("TIMEOUT -> RESEND")
                for seq in range(self.base, self.nextseq):
                    if not self.acked[seq]:
                        self.in_flight.add(seq)
                        self.color_packet(seq, "orange")  # timeout resend
                # reset timer
                self.timeouts["base"] = time.time()

    def deliver_and_ack(self):
        # simulate network + receiver
        self.set_receiver_state("WAIT_FOR_PKT")

        if not self.in_flight:
            return

        # pick some  pkts
        arrived = []
        for seq in list(self.in_flight):
            # random loss
            if random.random() < self.loss_prob:
                # lost
                self.color_packet(seq, "red")
                self.in_flight.remove(seq)
            else:
                # delivered
                arrived.append(seq)
                self.in_flight.remove(seq)

        # receiver handles packets
        for seq in arrived:
            if seq == self.base:
                # in order
                self.set_receiver_state("DELIVER_IN_ORDER")
                self.acked[seq] = True
                self.color_packet(seq, "lightgreen")
                self.base += 1
                # move base over already acked
                while self.base < self.num_packets and self.acked[self.base]:
                    self.base += 1
            elif seq > self.base:
                # buffered out of order
                self.set_receiver_state("BUFFER_OUT_OF_ORDER")
                self.acked[seq] = True
                self.color_packet(seq, "yellow")
            else:
                # old packet
                self.set_receiver_state("OLD_PKT")

        # if window moved, reset timer
        if self.base == self.nextseq:
            # all done or window empty
            self.timeouts["base"] = time.time()
        else:
            self.timeouts["base"] = time.time()

    def check_done(self):
        if self.base >= self.num_packets:
            if not self.done:
                self.done = True
                total = time.time() - self.start_time
                self.set_sender_state("DONE")
                self.set_receiver_state("DONE")
                self.lbl_status.config(text=f"Transfer done in {total:.3f} seconds")
            return True
        return False

    def step(self):
        # main simulation
        if self.done:
            return

        self.lbl_info.config(
            text=f"base={self.base}, nextseq={self.nextseq}, loss={self.loss_prob*100:.0f}%"
        )
        self.lbl_window.config(
            text=f"Window: [{self.base} .. {min(self.base+self.win_size-1, self.num_packets-1)}]"
        )

        # 1) send new packets inside window
        self.send_new_packets()

        # 2) randomly deliver
        self.deliver_and_ack()

        # 3) check timeout
        self.maybe_timeout()

        # 4) check finish
        if not self.check_done():
            self.root.after(self.step_ms, self.step)


if __name__ == "__main__":
    root = tk.Tk()
    app = GBNGui(root)
    root.mainloop()