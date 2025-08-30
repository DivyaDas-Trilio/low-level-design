from operator import add
import socket

def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr}:{conn} connected.")
    while True:
        try:
            msg = conn.recv(1024).decode('utf-8')
            if not msg:
                break
            print(f"[{addr}] {msg}")
            conn.sendall(f"Server Received: {msg}".encode('utf-8'))
        except:
            break
    conn.close()
    print(f"[Disconnected] {addr} left.")
        


def start_server():
    host = '192.168.1.44'
    port = 5555
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen()
    
    print(f"LISTENING SErver running on {host}:{port}")
    
    while True:
        conn, addr = server.accept()
        handle_client(conn, addr)
        
if __name__ == '__main__':
    start_server()