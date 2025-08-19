import time, asyncio

async def keep_printing_1(num):
    for i in range(num):
        await asyncio.sleep(0.5)
        print('I am Printing from 1...')
        
async def keep_printing_2(num):
    for i in range(num):
        await asyncio.sleep(0.2)
        print('I am Printing from 2...')
        
async def main():
    await asyncio.gather(keep_printing_1((10)), 
                         keep_printing_2(10),
                         keep_printing_1((10)), 
                         keep_printing_2(10),
                         keep_printing_1((10)), 
                         keep_printing_2(10))
    # await asyncio.gather(keep_printing_1((10)), keep_printing_2(10))
    # await asyncio.gather(keep_printing_1((10)), keep_printing_2(10))
    # await asyncio.gather(keep_printing_1((10)), keep_printing_2(10))
        
if __name__ == '__main__':
    start = time.time()
    asyncio.run(main())
    end = time.time()
    print("Completed in {}".format(end-start))