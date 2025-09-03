import asyncio

counter = 0

async def increment():
    global counter
    while(counter<10):
        counter += 1
        await asyncio.sleep(1)
        print(f"Counter:- {counter}") 
        
async def decrement():
    global counter
    #count = 0
    while(counter < 10):
        #count += 1
        counter -= 1
        await asyncio.sleep(0.75)
        #print(f"Counter:- {counter}") 
        

async def main():
    await asyncio.gather(increment(), decrement())
    
if __name__ == '__main__':
    asyncio.run(main())
    print(counter)