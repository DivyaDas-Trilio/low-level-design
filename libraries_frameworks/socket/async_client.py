import asyncio

async def start_client():
    reader, writer = await asyncio.open_connection('192.168.1.44', 5555)

    try:
        while True:
            msg = input("Enter message (q to quit): ")
            if msg.lower() == 'q':
                break
            writer.write((msg + "\n").encode())
            await writer.drain()

            data = await reader.read(1024)
            print(f"[SERVER] {data.decode().strip()}")
    finally:
        writer.close()
        await writer.wait_closed()

if __name__ == "__main__":
    asyncio.run(start_client())
