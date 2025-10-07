import csv
import subprocess
import time

#CRC vs Checksum Results Table

loss_rates = [0, 5, 10, 20, 40, 60]   # in percent
file_to_send = "udpfile.jpg"  # your test file (≥500KB)
results_csv = "crc_vs_checksum_results.csv"


# Helper function to run a single test

def run_test(method, loss_rate):
    server_script = "server_crc16.py" if method == "CRC16" else "server_checksum.py"
    client_script = "client_crc16.py" if method == "CRC16" else "client_checksum.py"

    # Launch server first
    server = subprocess.Popen(["python", server_script], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(1.0)  # allow server to start

    # Launch client
    t0 = time.perf_counter()
    client = subprocess.Popen(
        ["python", client_script],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    out, err = client.communicate(timeout=60)
    t1 = time.perf_counter()

    # Kill server after transfer ends
    server.kill()

    # Extract retransmissions count from output if printed
    retrans = 0
    undetected = 0
    for line in out.splitlines():
        if "Retransmissions" in line:
            try:
                retrans = int(line.split(":")[1].strip())
            except:
                pass
        if "Undetected Errors" in line:
            try:
                undetected = int(line.split(":")[1].strip())
            except:
                pass

    completion_time = t1 - t0
    print(f"{method} @ {loss_rate}% loss → time={completion_time:.3f}s, retrans={retrans}, undetected={undetected}")
    return completion_time, retrans, undetected

with open(results_csv, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Method", "LossRate(%)", "CompletionTime(s)", "Retransmissions", "UndetectedErrors"])

    for method in ["Checksum", "CRC16"]:
        for rate in loss_rates:
            try:
                t, r, u = run_test(method, rate)
                writer.writerow([method, rate, f"{t:.3f}", r, u])
            except subprocess.TimeoutExpired:
                print(f"{method} @ {rate}% timed out")
                writer.writerow([method, rate, "TIMEOUT", "N/A", "N/A"])

print(f"\n✅ Results written to {results_csv}")
