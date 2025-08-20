import asyncio

async def f1(fut):
    for i in range(10):
        await asyncio.sleep(1)
    fut.set_result('Done...')
    
async def main():
    loop = asyncio.get_running_loop()
    fut = loop.create_future()
    asyncio.create_task(f1(fut))
    print(await fut)
    
asyncio.run(main())