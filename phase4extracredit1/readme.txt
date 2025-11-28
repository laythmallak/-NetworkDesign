Phase Four Reliable Data Transfer Read Me

Students names
Binyam Mahari, Katrina Wong, Layth Mallack

Project description
This project implements reliable data transfer over UDP.
It uses Stop and Wait, Go Back N, and Selective Repeat.
The program shows packet loss, bit errors, timeouts, and retransmissions.
Completion time is measured and used to create performance graphs.

FILES IN THIS FOLDER

stopAwait.py
Implements the Stop and Wait protocol.
Handles packet loss, ACK loss, bit errors, and timeout.

GbackN.py
Implements the Go Back N protocol with sliding window.
Retransmits packets when ACKs are missing.

SelectiveRe.py
Implements Selective Repeat protocol.
Retransmits only lost packets instead of the full window.

udpfile.jpg
Test file sent from client to server.

udpfile_received.jpg
File reconstructed by the server.

phase4extra1.csv
Contains completion time results for loss rates from 0 percent to 60 percent.

sw_plot.png
Stop and Wait performance graph.

gbn_plot.png
Go Back N performance graph.

sr_plot.png
Selective Repeat performance graph.

readme.txt
This file.

REQUIREMENTS

Python 3
Allow Python through firewall
matplotlib for plotting graphs

Install matplotlib if needed
py -3 -m pip install matplotlib

HOW TO RUN

Open two terminals.
One for the server and one for the client.
Use the same port number for both.

STOP AND WAIT

Server
py -3 stopAwait.py server 5000

Client
py -3 stopAwait.py client 127.0.0.1 5000 udpfile.jpg

GO BACK N

Server
py -3 GbackN.py server 5001

Client
py -3 GbackN.py client 127.0.0.1 5001 udpfile.jpg

SELECTIVE REPEAT

Server
py -3 SelectiveRe.py server 5002

Client
py -3 SelectiveRe.py client 127.0.0.1 5002 udpfile.jpg

TESTING SCENARIOS

The program supports five test scenarios.

1 No loss or error
2 ACK bit error
3 Data packet bit error
4 ACK packet loss
5 Data packet loss

To test different scenarios, change the error or loss probability values
inside the protocol code.
Set the value to 0.0 for a clean channel.
Increase the value to test loss or error behavior.

HOW TO MAKE GRAPHS

The CSV file stores completion times.
Graphs are created using Python and matplotlib.

Run the plotting script
py -3 plot_results.py

This creates the png graph files.

DESIGN

The client reads the file and breaks it into packets.
Packets are sent using the selected protocol.
The server receives packets and sends acknowledgments.
If packets or ACKs are lost, the client retransmits.
Stop and Wait sends one packet at a time.
Go Back N sends packets in a window and resends on timeout.
Selective Repeat resends only missing packets.
Completion time is measured at the client.



DISCUSSION

Stop and Wait is slow because it waits for every ACK.
Go Back N is faster but resends many packets after loss.
Selective Repeat performs best because it only resends lost packets.
As loss rate increases, completion time increases for all protocols.
Selective Repeat remains the most efficient at high loss rates.

