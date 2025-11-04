import csv
import matplotlib.pyplot as plt

csv_path = "receiver_driven_results.csv"

rates, times, kbps = [], [], []
with open(csv_path) as f:
    r = csv.DictReader(f)
    for row in r:
        rates.append(float(row["rate"]) * 100.0)
        times.append(float(row["total_time_s"]))
        kbps.append(float(row["kbps"]))

plt.figure()
plt.plot(rates, times, marker="o", label="mode 6")
plt.xlabel("Loss/Error Rate (%)")
plt.ylabel("Completion Time (s)")
plt.grid(); plt.legend()
plt.title("Receiver-Driven (Mode 6): Time vs Rate")
plt.savefig("receiver_driven_time.png", dpi=200)

plt.figure()
plt.plot(rates, [k/1000.0 for k in kbps], marker="o", label="mode 6")
plt.xlabel("Loss/Error Rate (%)")
plt.ylabel("Throughput (MB/s)")
plt.grid(); plt.legend()
plt.title("Receiver-Driven (Mode 6): Throughput vs Rate")
plt.savefig("receiver_driven_throughput.png", dpi=200)

print("Saved receiver_driven_time.png and receiver_driven_throughput.png")