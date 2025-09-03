import asyncio

e = asyncio.Event()
l = []
async def producer():
    for i in range(100):
        await asyncio.sleep(1)
        e.clear()
        l.append(i)
        e.set()
        await asyncio.sleep(0.5)

async def consumer():
    while True:
        await asyncio.sleep(2)
        await e.wait()
        print(l)

async def main():
    await asyncio.gather(
        producer(),
        consumer()
    )

if __name__ == '__main__':
    asyncio.run(main())