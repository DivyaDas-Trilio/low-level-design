import selectors
import socket

# Create a selector (OS will pick best available: epoll/kqueue/poll)
sel = selectors.DefaultSelector()

def accept(sock):
    conn, addr = sock.accept()             # should be ready
    print(f"[NEW CONNECTION] {addr}")
    conn.setblocking(False)
    # Register this client for read events
    sel.register(conn, selectors.EVENT_READ, read)

def read(conn):
    try:
        data = conn.recv(1024)
    except ConnectionResetError:
        data = None

    if data:
        msg = data.decode("utf-8")
        print(f"[{conn.getpeername()}] {msg}")
        conn.sendall(f"Server Received: {msg}".encode("utf-8"))
    else:
        print(f"[DISCONNECTED] {conn.getpeername()}")
        sel.unregister(conn)
        conn.close()

def start_server():
    host, port = "192.168.1.35", 5555

    # Setup server socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen()
    server.setblocking(False)

    # Register server for "accept new connection" events
    sel.register(server, selectors.EVENT_READ, accept)
    print(sel)

    print(f"[LISTENING] Server running on {host}:{port}")

    # --- Custom Event Loop ---
    while True:
        events = sel.select(timeout=None)  # blocks until at least one fd is ready
        for key, mask in events:
            callback = key.data            # we stored accept/read as 'data'
            callback(key.fileobj)          # call it with the ready socket

if __name__ == "__main__":
    start_server()
