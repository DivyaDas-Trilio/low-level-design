import asyncio

#lock = asyncio.Lock()
lock = asyncio.BoundedSemaphore(2)

async def print_name(name):
    await lock.acquire()
    for i in range(10):
        print(f"Name:- {name}")
        await asyncio.sleep(1)
    lock.release()
        

async def main():
    await asyncio.gather(
        print_name('DHONI'),
        print_name('KOHLI'),
        print_name('SACHIN'))
    
if __name__ == '__main__':
    asyncio.run(main())