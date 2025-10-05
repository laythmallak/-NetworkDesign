import csv
import matplotlib.pyplot as plt

xs, opt1, opt2, opt3 = [], [], [], []
with open("measurements.csv", newline="", encoding="utf-8-sig") as f:  # << add encoding
    r = csv.DictReader(f)
    for row in r:
        xs.append(int(row["error"]))
        def val(k):
            s = (row.get(k) or "").strip()
            return float(s) if s else None
        opt1.append(val("opt1"))
        opt2.append(val("opt2"))
        opt3.append(val("opt3"))

plt.figure()
plt.plot(xs, opt1, marker="o", label="Option 1: No errors")
plt.plot(xs, opt2, marker="o", label="Option 2: ACK bit-errors")
plt.plot(xs, opt3, marker="o", label="Option 3: DATA bit-errors")
plt.xlabel("Error / Bit-Error Rate (%)")
plt.ylabel("Completion Time (seconds)")
plt.title("RDT 2.2 — Completion Time vs Error Rate (udpfile.jpg)")
plt.grid(True)
plt.legend()
plt.savefig("results.png", dpi=180, bbox_inches="tight")
print("Saved results.png")