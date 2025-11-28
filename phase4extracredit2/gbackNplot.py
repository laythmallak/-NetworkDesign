import csv
import matplotlib.pyplot as plt

loss = []
gbn_mt = []

# Open your CSV file
with open("percenterror.csv", "r") as f:
    reader = csv.reader(f)

    # Skip the first row
    header = next(reader, None)

    # Now read each data row
    for row in reader:
        if len(row) < 2:
            continue
        # first column
        loss_val = row[0].strip()
        time_val = row[1].strip()
        if loss_val == "" or time_val == "":
            continue

        loss.append(int(loss_val))
        gbn_mt.append(float(time_val))

# Make the plot
plt.figure()
plt.plot(loss, gbn_mt, marker="o")

plt.xlabel("Loss / Error Rate (%)")
plt.ylabel("Completion Time (seconds)")
plt.title("Go-Back-N Multi-thread Completion Time vs Loss Rate")
plt.grid(True)

plt.savefig("GBN_MT_only.png", dpi=200)
plt.show()

print("Graph saved as GBN_MT_only.png")
