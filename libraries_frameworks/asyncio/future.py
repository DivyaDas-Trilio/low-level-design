import asyncio

async def f1(fut):
    await asyncio.sleep(1)
    await fut
    #fut.set_result('Done from f1')
    
async def f2(fut):
    await asyncio.sleep(2)
    fut.set_result('Done from f2')
    
async def main():
    loop = asyncio.get_running_loop()
    fut = loop.create_future()
    task1 = asyncio.create_task(f1(fut))
    task2 = asyncio.create_task(f2(fut))
    print(await fut)
    # print(fut.result())
    await asyncio.gather(task1, task2)
    
asyncio.run(main())