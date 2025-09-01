import asyncio, socket

# async def handle_client(reader, writer):
#     addr = writer.get_extra_info('peername')
#     print(f"[NEW CONNECTION] {addr}")

#     try:
#         while True:
#             data = await reader.read(1024)
#             if not data:  # client disconnected
#                 break
#             msg = data.decode().strip()
#             print(f"[{addr}] {msg}")
#             response = f"Server received: {msg}\n"
#             writer.write(response.encode())
#             await writer.drain()
#     except asyncio.CancelledError:
#         pass
#     finally:
#         print(f"[DISCONNECTED] {addr}")
#         writer.close()
#         await writer.wait_closed()

import asyncio
from os import read

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't need to be reachable, just used for routing
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

async def handle_client(reader, writer):
    # Read HTTP request from browser
    request = await reader.read(1024)
    request_text = request.decode()
    print("Received request:\n", request_text)
    print(f"IPAddress: {get_ip()}")
    ip_addr = get_ip()

    # Prepare a valid HTTP response
    response = (
        "HTTP/3 200 OK\r\n"
        "Content-Type: text/html; charset=utf-8\r\n\r\n"
        f"<h1>Hello from Asyncio Server 🚀 from {ip_addr}</h1>"
    )

    # Send response back to browser
    writer.write(response.encode())
    await writer.drain()
    writer.close()
    await writer.wait_closed()


async def start_server():
    HOST= "0.0.0.0"
    PORT = 8443
    server = await asyncio.start_server(handle_client, HOST, PORT)
    addr = server.sockets[0].getsockname()
    print(f"[LISTENING] server on {addr}")
    async with server:
        await server.serve_forever()
        
if __name__ == '__main__':
    asyncio.run(start_server())
