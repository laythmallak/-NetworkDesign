Phase Four GoBackN MultiThreaded GUI Read Me
Students name Binyam Mahari, layth mallak and katrina wong


Go-Back-N multithreaded sender and receiver with GUI.
Shows window-based reliable data transfer with packet loss.
GUI shows real-time sender and receiver FSM behavior.
Used to study performance vs loss from 0% to 60%.

FILES IN THIS FOLDER


GbackNGui.py
GUI program that visualizes Go-Back-N protocol behavior.
Shows packets moving, ACKs received, and window sliding.

udpfile.jpg
Test file sent from client to server.

GbackNGuiplot.csv
CSV version of loss vs completion time.

plotGui.py
Python script to plot loss versus completion time.

GbackNGuiplot_graph.png
Graph image showing completion time vs loss percentage.

readme.txt
This file.


REQUIREMENTS

Python three

matplotlib for graphs


Install matplotlib if needed:
py -3 -m pip install matplotlib


HOW TO RUN

Start server first, then client.
Pick a port, example 5003.
Use same port on both.

SERVER
py -3 GbackN_mt.py server 5003

CLIENT
py -3 GbackN_mt.py client 127.0.0.1 5003 udpfile.jpg


HOW TO RUN GUI

py -3 GbackNGui.py


LOSS TESTING (GUI)

Open GbackNGui.py.


self.loss_prob = 0.0
self.loss_prob = 0.2
self.loss_prob = 0.6

Run GUI again and record completion time.
Store results in excel.


HOW TO MAKE GRAPH

py -3 plotGui.py

Creates GbackNGuiplot_graph.png


DESIGN

The client splits the file into packets and sends them using
a sliding window Go-Back-N protocol.
Multiple threads are used:
One thread sends packets in the window.
One thread listens for ACKs.
One thread handles timeout and retransmission.

The server receives packets in order and sends ACKs.
If a packet is lost, all packets after it are retransmitted.

The GUI visualizes packet sending, loss events, ACK reception,
and window movement.
This helps understand how Go-Back-N works internally.

As loss increases, more retransmissions occur and completion
time increases.


DISCUSSION AND OBSERVATIONS

 GoBackN performs fast at low loss because multiple packets
 are sent before waiting for ACKs.
 At high loss, performance degrades because many packets
 must be retransmitted.
 Multi-threading improves speed compared to single threaded
 Go Back N by allowing parallel send, receive, and timer logic.
 GUI visualization helps clearly understand protocol behavior.
 Stop-and-Wait is slowest, Selective Repeat is fastest,
  Go-Back-N is in between.


This implementation satisfies
Window-based protocol implementation
Multithreaded sender and receiver
GUI with FSM visualization
Performance measurement from 0% to 60% loss