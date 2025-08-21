import asyncio, time

async def producer(q):
    for i in range(1,6):
        await asyncio.sleep(0.5)
        item = f"Item-{i}"
        print(f"Produced {item}")
        await q.put(item)
    await q.put(None)

async def consumer(q):
    while True:
        item = await q.get()
        if item is None:
            break
        await asyncio.sleep(0.5)
        print(f"{item} consumed.")

async def main():
    start = time.time()
    queue = asyncio.Queue()
    await asyncio.gather(producer(queue), consumer(queue))
    end = time.time()
    print(f"Elapsed Time:- {end-start}")
    
asyncio.run(main())