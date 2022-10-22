import socket

def get_host_ip():
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)
    return ip

hostName = get_host_ip()
serverPort = 8080

print(hostName)