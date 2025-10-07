group names: Binyam mahari, katrina  Wong, Layth Mallak

File name	     Purpose
clientco.py	    UDP sender implementing RDT 2.2 (alternating bit, checksum, retransmit). Can simulate ACK bit errors (Option 2).
serverco.py	     UDP receiver implementing RDT 2.2. Can simulate DATA bit errors (Option 3).
udpfile.jpg	          Example file to send (≥500 KB recommended).
udpfile_received.jpg	Output file created on receiver side after a run (should match udpfile.jpg).
measurements.csv	     Table of measured completion times for Options 1–3 at 0%–60% error/loss (can be created manually or via script).
plotchart.py	        Reads measurements.csv and generates results.png (chart of Completion Time vs Error Rate).
results.png	            Chart image generated from plotchart.py for your report.

How to Set Up and Run
1. Requirements

Python 3.8+ installed

Both client and server scripts in the same folder

A test file to send (e.g., udpfile.jpg ≥500 KB)


 Running normal transfer


Start the receiver

python serverco.py

Start the sender

python clientco.py

Watch the console for:

Server: Wrote: udpfile_received.jpg (...) bytes

Client: TOTAL_TIME_SEC: ...

Confirm udpfile_received.jpg matches original file size.

testing different scenarios

Option 1 — No Loss / Error

Server:
python serverco.py

Client:
python clientco.py

Option 2 — ACK Bit Errors

Server: normal (no data error)
python serverco.py


Client: add --ackp with error probability (0–1)
Example for 5%:

python clientco.py --ackp 0.05
Repeat with 0%, 5%, 10%, …, 60% and record TOTAL_TIME_SEC

option 3
Option 3 — DATA Bit Errors

Server: add -datap with error probability (0–1)
Example for 5%:

python serverco.py -datap 0.05

Client: normal (no ACK error)

python clientco.py
Repeat with 0%, 5%, 10%, …, 60% and record TOTAL_TIME_SEC

Fill in measurements.csv with your recorded times in the format:

error,opt1,opt2,opt3
0,0.374,,
5,,0.358,0.342
10,,0.430,0.351
...
60,,0.591,0.743

Run:
python plotchart.py
