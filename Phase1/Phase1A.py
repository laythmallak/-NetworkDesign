from socket import *
serverName = "localhost"
serverPort = 12000
clientSocket = socket(AF_INET, SOCK_DGRAM)
message = input("Input lowercase sentence:")
clientSocket.sendto(message.encode(),(serverName, serverPort))
modifiedMessage, serverAddress = clientSocket.recvfrom(2048)
print (modifiedMessage.decode())
clientSocket.close()


#a program to send and receive UDP packets


#A Socket is a doorway through which data can be sent and received
#A Socket is bound to a port number so that the Transmission Control Protocol (TCP) layer
#can identify the application that data is destined to be sent to
#A UDP socket is defined by an IP address and a port number
#A UDP socket is used to send and receive datagrams