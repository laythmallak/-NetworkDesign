#!/usr/bin/env python3
"""
run_sweep.py — Phase 3 Section 1 automation
--------------------------------------------------------------------------------------
Runs Options 1–5 across rates 0..60% (step 5% by default), averages N trials,
and writes measurements.csv with completion time and throughput columns.
-------------------------------------------------------------------------------------
Examples:
  py run_sweep.py --file udpfile.jpg --runs 1 --start 0 --end 0 --rto 0.04 --verbose
  py run_sweep.py --file udpfile.jpg --runs 3 --rto 0.04
"""

import argparse, subprocess, sys, time, os, re, csv
from statistics import mean

# helpers 
TIME_RE = re.compile(r"TOTAL_TIME_SEC:\s*([0-9.]+)")

def parse_time_from_stdout(s: str):
    m = TIME_RE.search(s or "")
    return float(m.group(1)) if m else None

def run_one(server_mode: int, client_mode: int, rate: float, args):
    """
    Start server -> run client -> stop server -> parse client time -> compute throughput.
    Returns (time_seconds or None, throughput_bytes_per_sec or None).
    """
    py = sys.executable
    port = str(args.port)

    server_cmd = [
        py, "-u", "serverco.py",
        "--mode", str(server_mode),
        "--rate", f"{rate:.4f}",
        "--port", port,
        "--outfile", args.outfile
    ]
    client_cmd = [
        py, "-u", "clientco.py",
        "--mode", str(client_mode),
        "--rate", f"{rate:.4f}",
        "--server", args.server,
        "--port", port,
        "--file", args.file,
        "--rto", str(args.rto)
    ]

    # 1) Start server
    srv = subprocess.Popen(server_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    time.sleep(0.3)  # small bind delay

    # 2) Run client
    cli = subprocess.run(client_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    client_out = cli.stdout or ""

    # 3) Stop server and collect stdout so it doesnt hang
    try:
        srv.terminate()  # ask nicely
        try:
            server_out, _ = srv.communicate(timeout=1.0)
        except subprocess.TimeoutExpired:
            srv.kill()    # force if needed
            server_out, _ = srv.communicate(timeout=1.0)
    except Exception:
        try:
            server_out = srv.stdout.read() if srv.stdout else ""
        except Exception:
            server_out = ""

    if args.verbose:
        print("\n--- CLIENT OUT ---\n", client_out)
        print("\n--- SERVER OUT ---\n", server_out)

    # 4) Time from client, compute throughput
    t = parse_time_from_stdout(client_out)
    thr = None
    try:
        fsize = os.path.getsize(args.file)
        thr = (fsize / t) if (t and t > 0) else None
    except Exception:
        pass

    return t, thr

def avg_or_none(values):
    vs = [v for v in values if v is not None]
    return (mean(vs) if vs else None)

# main
def main():
    ap = argparse.ArgumentParser(description="Sweep Options 1–5 and loss/error rates for Phase 3 Section 1")
    ap.add_argument("--server", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=12007)
    ap.add_argument("--file", default="udpfile.jpg", help="≥500 KB file per spec")
    ap.add_argument("--outfile", default="udpfile_received.jpg")
    ap.add_argument("--rto", type=float, default=0.04, help="sender timeout (sec); use ~0.03–0.05 for measurements")
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--end", type=int, default=60)
    ap.add_argument("--step", type=int, default=5)
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--csv", default="measurements.csv")
    ap.add_argument("--verbose", action="store_true", help="print raw client/server output for debugging")
    args = ap.parse_args()

    header = [
        "error",
        "opt1_time","opt2_time","opt3_time","opt4_time","opt5_time",
        "opt1_thr","opt2_thr","opt3_thr","opt4_thr","opt5_thr"
    ]
    rows = []

    rate_points = list(range(args.start, args.end + 1, args.step))
    for p in rate_points:
        rate = p / 100.0
        # Mapping: (server_mode, client_mode)
        mapping = [
            (1,1),  # Opt1: No errors
            (1,2),  # Opt2: ACK bit-errors (sender)
            (3,1),  # Opt3: DATA bit-errors (receiver)
            (1,4),  # Opt4: ACK loss (sender)
            (5,1),  # Opt5: DATA loss (receiver)
        ]

        times_averaged = []
        thrs_averaged  = []

        for sm, cm in mapping:
            t_runs, thr_runs = [], []
            for _ in range(args.runs):
                t, thr = run_one(sm, cm, rate, args)
                if t is not None:   t_runs.append(t)
                if thr is not None: thr_runs.append(thr)
            times_averaged.append(avg_or_none(t_runs))
            thrs_averaged.append(avg_or_none(thr_runs))

        print(f"RATE {p:2d}% -> times(s): {times_averaged}  thr(bps): {thrs_averaged}")
        rows.append([p] + times_averaged + thrs_averaged)

    # Write CSV file
    with open(args.csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"\nWrote {args.csv} with {len(rows)} rows.")

if __name__ == "__main__":
    main()
