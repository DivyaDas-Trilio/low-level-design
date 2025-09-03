import asyncio

counter = 0
async_lock = asyncio.Lock()

async def increment():
    await async_lock.acquire()
    global counter
    while(counter<10):
        counter += 1
        await asyncio.sleep(1)
        print(f"Counter:- {counter}") 
    async_lock.release()
        
async def decrement():
    await async_lock.acquire()
    global counter
    #count = 0
    while(counter < 10):
        #count += 1
        counter -= 1
        await asyncio.sleep(0.75)
        #print(f"Counter:- {counter}")
    async_lock.release() 
        

async def main():
    await asyncio.gather(increment(), decrement())
    
if __name__ == '__main__':
    asyncio.run(main())
    print(counter)