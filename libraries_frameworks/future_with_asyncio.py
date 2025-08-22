import asyncio

async def worker(name, delay):
    print(name)
    await asyncio.sleep(delay)
    print(f"Task Finished after {delay} sec")
    if name == 'B':
        raise ValueError()
    return f"Result from task - {name}"

async def main():
    task1 = asyncio.create_task(worker("A", 2))
    task2 =  asyncio.create_task(worker("B", 2))
    task3 =  asyncio.create_task(worker("C", 2))
    task4  = asyncio.create_task(worker("D", 2))
    
    result = await asyncio.gather(task1, task2, task3, task4)
    print(result)
    print(type(result))
    
asyncio.run(main())