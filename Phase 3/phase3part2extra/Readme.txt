Phase Three Part Two Stop and Wait RDT Read Me
Students name Binyam Mahari, layth mallak and katrina wong


Stop and wait send and receive.
Shows bit errors, loss, timeout, and saves results for graphs.

FILES IN THIS FOLDER

server dot py receives data, writes file, can drop or damage data
client dot py sends data, waits for ack, can drop or damage ack
udpfile dot jpg test file that is sent between programs
measurements part two dot csv results for five main test runs
rto study dot csv results when timeout value changes
ack eff dot csv results when ack loss value changes
plot dot py makes picture graphs using results
rto vs retransmissions dot png picture of timeout and retries
rto vs time dot png picture of timeout and time
ack efficiency vs loss dot png picture of ack loss and use rate
time vs ack loss dot png picture of time and ack loss
retrans vs ack loss dot png picture of retries and ack loss
read me dot txt this file, instructions

REQUIREMENTS

Python three
Allow python in firewall
matplotlib for graphs
Install
py three m pip install matplotlib

HOW TO RUN

Start server first, then client
Pick a port, example one two zero zero eight
Use same port on both

Option one clean channel
Server
py three server dot py mode one rate zero port one two zero zero eight
Client
py three client dot py mode one rate zero server one two seven dot zero dot zero dot one port one two zero zero eight file udpfile dot jpg rto zero point zero four csv measurements part two dot csv

Option two ack bit errors
Server
py three server dot py mode one rate zero port one two zero zero eight
Client
py three client dot py mode two rate zero point one zero server one two seven dot zero dot zero dot one port one two zero zero eight file udpfile dot jpg rto zero point zero four csv measurements part two dot csv

HOW TO MAKE GRAPHS

py three plot dot py

Creates the png picture files

design
The client reads the file and sends one packet at a time to the server.
The server receives the packet and writes the data into a new file.
After each packet, the server sends back a small ack message.
If the client does not get the correct ack, it sends the same packet again.
A timeout timer decides when to resend a packet that looks lost.
Error and loss rates change how often packets or acks fail, which can slow down the transfer.

discussion questions
1; Variable packet size can make sending faster when the network is good and slower when the network is bad.
2; Adaptive timeout can wait the right time and resend fewer packets.
3; High packet loss makes many packets disappear and need more resend.
4; Changing packet size and timeout can save time and make the network more fair.

discussion questions
1; Receiver driven can avoid overload but may be slower.
2; Receiver driven sends less when the network is busy, so less traffic.
3; Good for streaming and cloud files where the receiver chooses the speed.