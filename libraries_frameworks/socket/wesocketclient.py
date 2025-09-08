import asyncio
import websockets

async def client():
    async with websockets.connect("ws://127.0.0.1:7001") as ws:
        while True:
            reply = await ws.recv()
            print("WebSocket client received:", reply)
            inp = input("Enter message:- ")
            await ws.send(f"From Client:- {inp}")

asyncio.run(client())
