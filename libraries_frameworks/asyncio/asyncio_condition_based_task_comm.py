import asyncio

c = asyncio.Condition()
l = []
async def producer():
    await c.acquire()
    for i in range(20):
        await asyncio.sleep(5)
        l.append(i)
        c.notify()
    c.release()
        

async def consumer():
    while True:
        print('Consumer is waiting...')
        await asyncio.sleep(1)
        c.wait()
        print(l)
        

async def main():
    await asyncio.gather(
        producer(),
        consumer()
    )

if __name__ == '__main__':
    with asyncio.Runner() as runner:
        runner.run(main())