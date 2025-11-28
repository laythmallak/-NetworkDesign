import csv
import matplotlib.pyplot as plt

loss = []
sw = []
gbn = []
sr = []

# read CSV file
with open("phase4extra1.csv", "r") as f:
    reader = csv.reader(f)
    next(reader)

    for row in reader:
        loss.append(int(row[0]))
        sw.append(float(row[1]))
        gbn.append(float(row[2]))
        sr.append(float(row[3]))

# Stop and Wait graph
plt.figure()
plt.plot(loss, sw, marker="o")
plt.xlabel("Loss Rate (%)")
plt.ylabel("Completion Time (s)")
plt.title("Stop and Wait Performance")
plt.grid(True)
plt.savefig("sw_plot.png")

# GoBackN graph
plt.figure()
plt.plot(loss, gbn, marker="o")
plt.xlabel("Loss Rate (%)")
plt.ylabel("Completion Time (s)")
plt.title("Go-Back-N Performance")
plt.grid(True)
plt.savefig("gbn_plot.png")

#  Selective Repeat graph
plt.figure()
plt.plot(loss, sr, marker="o")
plt.xlabel("Loss Rate (%)")
plt.ylabel("Completion Time (s)")
plt.title("Selective Repeat Performance")
plt.grid(True)
plt.savefig("sr_plot.png")

plt.show()