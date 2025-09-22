# Phase 1 – UDP Message/File Transfer

## Authors
- [Layth Mallak]
- [Group Members: Layth Mallak]

### Project Phase 1: Parts A and B

This code implements parts A and B of the project:

###PART A- A simple UDP sender and receiver
-
#--Phase1A.py 
-A Simple UDP Client that sends a lowercase sentence to the server and waits for the response.
-
#--Phase1AServer.py
-A simple UDP server. It receives a message from the client, and sends it back to the client.
-

###PART B
-
#--phase1Bclient.py 
- A client for sending a file. It reads a file, splits it into 1024-byte chunks,
-sends a meta packet containing information about the incoming file,
-then sends data packets carrying the contents of the file
-
#--phase1AServer.py
- A server that receives data fr4om the client. It listens on UDP port 5051.
-The server receives a meta packet containing information on the file.
-Then it receives data packets, which are reassembled to create the file.
-

####

### Environment
# **Operating System: Windows 10  
# **Programming Language**: Python  
# **Version**: Python 3.13 
# **IDE/Editor Used**: Visual Studio Code
---

####

### Instructions

#--Part A- UDP message

#1. Start the server by putting --

-> py Phase1AServer.py

#2. You should see 

--> The server is ready to receive

#3. Start the client in another terminal with --

-> py Phase1A.py

#4. The client will ask you to input a message.

#5 After inputting the message the server should echo it back to you.

##

#--Part B- EDUP file transfer

#1. Start the server by putting --

-> py phase1BServer.py

#2. You should see 

--> [SERVER] UDP listening on 0.0.0.0:5051


#3. Start the client in another terminal with --

-> py phase1Bclient.py

#4. A prompt will appear asking you to enter the path of the file. Example --

-> C:\Users\[username]\Desktop\Python\testfile.bmp

#5. The client will display sending progress, and the server will display receiving process.

#6. The server will save the sent file in the same file as where the server is located. 


