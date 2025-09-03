import asyncio

q = asyncio.Queue()

async def producer():
    for i in range(100):
        await q.put(i)
        await asyncio.sleep(2)

async def consumer():
    while True:
        item = await q.get()
        print(item)

async def main():
    await asyncio.gather(
        producer(),
        consumer()
    )
    
if __name__ == '__main__':
    with asyncio.Runner() as runner:
        runner.run(main())