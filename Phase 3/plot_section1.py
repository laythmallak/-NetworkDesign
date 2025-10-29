import matplotlib.pyplot as plt, csv

xs=[]; data=[]
with open("measurements.csv") as f:
    r=csv.DictReader(f)
    for row in r:
        xs.append(int(row["error"]))
        data.append(row)

labels = ["opt1","opt2","opt3","opt4","opt5"]

def get(series):
    return [None if row[f"{series}_time"]=="" else float(row[f"{series}_time"]) for row in data]

plt.figure()
for s in labels:
    plt.plot(xs, get(s), marker="o", label=s)
plt.xlabel("Error/Loss Rate (%)")
plt.ylabel("Completion Time (s)")
plt.grid(); plt.legend()
plt.title("Completion Time vs Error/Loss")
plt.savefig("results_time.png",dpi=200)

def get_thr(series):
    return [None if row[f"{series}_thr"]=="" else float(row[f"{series}_thr"])/1e6 for row in data]

plt.figure()
for s in labels:
    plt.plot(xs, get_thr(s), marker="o", label=s)
plt.xlabel("Error/Loss Rate (%)")
plt.ylabel("Throughput (MB/s)")
plt.grid(); plt.legend()
plt.title("Throughput vs Error/Loss")
plt.savefig("results_throughput.png",dpi=200)

print("Saved results_time.png and results_throughput.png")
