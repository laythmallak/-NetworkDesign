import matplotlib.pyplot as plt


rto_values = [0.03, 0.05, 0.07, 0.10]
retransmissions = [229, 216, 219, 200]
times_sec = [10.344901, 13.915473, 18.483351, 23.712018]

# Plot 1: RTO vs Retransmissions
plt.figure()
plt.plot(rto_values, retransmissions, marker="o")
plt.xlabel("RTO (seconds)")
plt.ylabel("Retransmissions (count)")
plt.title("RTO vs Retransmissions (ACK loss = 10%)")
plt.grid(True)
plt.savefig("rto_vs_retransmissions.png", dpi=200)
plt.close()

# Plot 2: RTO vs Total Time
plt.figure()
plt.plot(rto_values, times_sec, marker="o")
plt.xlabel("RTO (seconds)")
plt.ylabel("Total Time (seconds)")
plt.title("RTO vs Total Time (ACK loss = 10%)")
plt.grid(True)
plt.savefig("rto_vs_time.png", dpi=200)
plt.close()


# 0%:  time=0.781764, retrans=0,    eff=1.000
# 10%: time=11.014293, retrans=200, eff=1.000
# 20%: time=24.670670, retrans=482, eff=1.000
# 40%: time=62.608967, retrans=1325,eff=1.000
# 60%: time=110.000000, retrans=2500,eff=1.000
loss_rates = [0, 10, 20, 40, 60]  # percent
ack_efficiency = [1.000, 1.000, 1.000, 1.000, 1.000]
total_time = [0.781764, 11.014293, 24.670670, 62.608967, 110.000000]
retrans = [0, 200, 482, 1325, 2500]

# Plot 3: Loss % vs ACK Efficiency
plt.figure()
plt.plot(loss_rates, ack_efficiency, marker="o")
plt.xlabel("ACK Loss Rate (%)")
plt.ylabel("ACK Efficiency (useful/total)")
plt.title("ACK Efficiency vs ACK Loss")
plt.ylim(0, 1.05)
plt.grid(True)
plt.savefig("ack_efficiency_vs_loss.png", dpi=200)
plt.close()

# Plot 4: Loss % vs Total Time
plt.figure()
plt.plot(loss_rates, total_time, marker="o")
plt.xlabel("ACK Loss Rate (%)")
plt.ylabel("Total Time (seconds)")
plt.title("Total Time vs ACK Loss")
plt.grid(True)
plt.savefig("time_vs_ack_loss.png", dpi=200)
plt.close()

# Plot 5: Loss % vs Retransmissions
plt.figure()
plt.plot(loss_rates, retrans, marker="o")
plt.xlabel("ACK Loss Rate (%)")
plt.ylabel("Retransmissions (count)")
plt.title("Retransmissions vs ACK Loss")
plt.grid(True)
plt.savefig("retrans_vs_ack_loss.png", dpi=200)
plt.close()

print("Saved 5 graphs:\n - rto_vs_retransmissions.png\n - rto_vs_time.png\n - ack_efficiency_vs_loss.png\n - time_vs_ack_loss.png\n - retrans_vs_ack_loss.png")