import socket


def start_client():
    HOST = "192.168.1.44"
    PORT = 5555
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))
    
    try:
        while True:
            msg = input("Enter Message(q to Quit): ")
            if msg.lower() == 'q':
                break
            
            client.sendall(msg.encode('utf-8'))
            response = client.recv(1024).decode('utf-8')
            print(f"[SERVER] {response}")
    finally:
        client.close()
        
if __name__ == '__main__':
    start_client()