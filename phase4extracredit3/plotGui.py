import csv
import matplotlib.pyplot as plt

# your CSV file name
CSV_FILE = "GbackNGuiplot.csv"

loss = []   # x axis
time = []   # y axis

# read data from csv file
with open(CSV_FILE, newline="") as f:
    reader = csv.reader(f)
    header = next(reader)  # skip header line

    for row in reader:
        if len(row) < 2:
            continue
        # first column = loss, second column = time
        loss_val = float(row[0])
        time_val = float(row[1])

        loss.append(loss_val)
        time.append(time_val)

# make a line graph
plt.figure()
plt.plot(loss, time, marker="o")

plt.xlabel("Loss percentage (%)")
plt.ylabel("Completion time (seconds)")
plt.title("Go-Back-N GUI: Completion Time vs Loss Rate")
plt.grid(True)

# save picture and also show it
plt.savefig("GbackNGuiplot_graph.png")
plt.show()