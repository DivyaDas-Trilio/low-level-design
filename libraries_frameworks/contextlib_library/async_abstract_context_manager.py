import asyncio

class MyAsyncAbstractContextManager:
    def __init__(self):
        print("Init...")
        
    async def __aenter__(self):
        print("aenter ...")
        return self
    
    async def __aexit__(self, exc_type, exc_val, traceback):
        print("aexit...")
        
async def main():
      async with MyAsyncAbstractContextManager() as acntx:
        print('inside async context manager.') 

if __name__ == "__main__":
    asyncio.run(main())