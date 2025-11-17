import time
import matplotlib.pyplot as plt
import csv

def runSender(packet_size):
    time.sleep(0.01)  # replace with your sender.send(size)
    return

packet_sizes = [100, 200, 400, 500]
completiontimes = []

for size in packet_sizes:
    start = time.time()
    runSender(size)
    end = time.time()
    completiontimes.append(end - start)

# Save CSV
csvFile = "measurements.csv"
with open(csvFile, "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["Packet Size", "Completion Time (s)"])
    for size, t in zip(packet_sizes, completiontimes):
        writer.writerow([size, t])

# plot 1
plt.figure()   # <-- Important: new figure for each plot
plt.plot(packet_sizes, completiontimes, marker="o")
plt.xlabel("Packet Size (bytes)")
plt.ylabel("Completion Time (seconds)")
plt.title("Completion Time vs Packet Size")
plt.grid(True)
plt.savefig("plot1.png",dpi=200)

# plot 2
window_sizes = [1,2,5,10,20]
window_times = [0.05,0.04,0.03,0.02,0.025]  # replace with your measurements

plt.figure()   # <-- new figure
plt.plot(window_sizes, window_times, marker="s", color="red")
plt.xlabel("Window Size")
plt.ylabel("Completion Time (s)")
plt.title("Completion Time vs Window Size")
plt.grid(True)
plt.savefig("plot2.png",dpi=200)

# plot 3
timeouts_ms = [10,20,30,40,50]
timeout_times = [0.03,0.025,0.02,0.022,0.021]  # replace with measurements

plt.figure()
plt.plot(timeouts_ms, timeout_times, marker="^", color="green")
plt.xlabel("Timeout (ms)")
plt.ylabel("Completion Time (s)")
plt.title("Completion Time vs Timeout")
plt.grid(True)
plt.savefig("plot3.png",dpi=200)

#plot 4
phases = ["Phase 2", "Phase 3", "Phase 4"]
phase_times = [2.35, 1.78, 0.10]
x = range(len(phases))
plt.figure(figsize=(9,6))
plt.plot(x, phase_times, marker='o', linestyle='-', color='blue')
for i, t in enumerate(phase_times):
    plt.text(i, t + 0.02, f"{t:.2f}", ha='center', va='bottom')

plt.xticks(x, phases)  # Label X-axis with phase names
plt.xlabel("Phase")
plt.ylabel("File Transfer Completion Time (s)")
plt.title("Chart 4: Phase Performance Comparison at 20% Loss/Error")
plt.grid(True)
plt.tight_layout()
plt.show()
plt.savefig("plot4.png",dpi=200)



