import asyncio, time

async def printing(num):
    await asyncio.sleep(0.5)
    print(num)

async def f1():
    for i in range(10):
        await printing(i)
        
async def f2():
    for j in range(11,20):
        await printing(j)
        
async def async_main():
    await asyncio.gather(f1(), f2())
        
if __name__ == '__main__':
    start = time.time()
    with asyncio.Runner() as runner:
        runner.run(async_main())
    end = time.time()
    print('Elapsed Time:- {}'.format(end-start))