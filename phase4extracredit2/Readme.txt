Phase Four Extra Credit part 2
Multi-Threaded Go Back N Read Me

Students name
Binyam Mahari, Layth Mallak, Katrina Wong

Multithreaded Go-Back-N reliable data transfer program.
Uses separate threads for sending, receiving ACKs, and managing retransmission timer.
Shows performance improvement compared to single-threaded Go Back N.

FILES IN THIS FOLDER

GbackN_mt.py
Multithreaded Go Back N sender and receiver implementation.
Uses threads for sending packets, receiving ACKs, and handling timeout logic.

udpfile.jpg
Test file that is transferred from client to server.

percenterror.csv
Completion time results for loss rates from 0% to 60% in steps of 5%.



gbackNplot.py
Python script to plot completion time vs loss rate.

GBN_MT_only.png
Graph showing multithreaded Go Back N performance.

readme.txt
This file.

REQUIREMENTS

Python three

matplotlib for graphs

Install matplotlib if needed
py -3 -m pip install matplotlib

HOW TO RUN

Start server first, then client.
Pick a port number, example 5000.
Use the same port on both server and client.

Server
py -3 GbackN_mt.py server 5003

Client
py -3 GbackN_mt.py client 127.0.0.1 5003 udpfile.jpg

The program prints packet sends, ACK receives, and final completion time.

HOW TO TEST DIFFERENT LOSS RATES

Loss rates are tested from 0% to 60% in steps of 5%.
Loss probability is changed inside the code before running each test.
Completion time is recorded and saved into CSV and Excel files.

HOW TO MAKE GRAPHS

After running all tests and saving data:

py -3 gbackNplot.py

This creates the PNG graph for multithreaded GoBackN performance.

DESIGN

The client reads the file and splits it into packets.
GoBackN uses a sliding window to send multiple packets.

Three threads are used:
 Sending thread sends packets inside the window.
 Receiving thread listens for ACKs.
 Timer thread handles retransmissions on timeout.

Locks are used to protect shared variables such as base and next sequence number.
This avoids race conditions between threads.

The server receives packets, writes data to a file, and sends cumulative ACKs.

DISCUSSION
 Multithreading improves throughput by removing idle waiting.
 ACK receiving does not block packet sending.
 Performance is better than single threaded GoBackN, especially under loss.
 Higher loss causes longer completion time, but multithreaded design reduces delay.