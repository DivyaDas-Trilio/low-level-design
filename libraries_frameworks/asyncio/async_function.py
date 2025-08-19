import time
import asyncio

async def compute1(num):
    print('starting compute1...')
    await asyncio.sleep(5)
    print('Ending compute1...')
       
async def compute2(num):
    print('starting compute2...')
    await asyncio.sleep(5)
    print('Ending compute2...')
    
async def main():
    await asyncio.gather(
        compute1(5), 
        compute2(5)
    )
   
    
if __name__ == '__main__':
    start = time.time()
    asyncio.run(main())
    end = time.time()
    print("Completed in {}".format(end-start))