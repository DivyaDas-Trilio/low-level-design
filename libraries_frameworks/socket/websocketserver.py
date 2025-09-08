import asyncio
import websockets

async def handler(websocket):
    print("WebSocket client connected")
    #await websocket.send("Hello from WebSocket server!")
    #count = 0
    while True:
        inp = input("Enter mes-age:")
        await websocket.send(f"from server:- {inp}")
        reply = await websocket.recv()
        print(reply)

async def main():
    async with websockets.serve(handler, "127.0.0.1", 7001):
        print("WebSocket server listening on 7001...")
        await asyncio.Future()

asyncio.run(main())
