import asyncio

# class MyAsyncAbstractContextManager:
#     def __init__(self):
#         print("Init...")
        
#     async def __aenter__(self):
#         print("aenter ...")
#         return self
    
#     async def __aexit__(self, exc_type, exc_val, traceback):
#         print("aexit...")
        
# async def main():
#       async with MyAsyncAbstractContextManager() as acntx:
#         print('inside async context manager.') 

# if __name__ == "__main__":
#     asyncio.run(main())


from contextlib import AbstractAsyncContextManager

class MyAsyncContextManager(AbstractAsyncContextManager):
    def __init__(self):
        print('init...')
        
    async def __aexit__(self, exc_type, exc_val, traceback):
        print('aexit...')
        

async def main():
    async with MyAsyncContextManager() as acntx:
        print('inside async context manager...')
        
if __name__ == "__main__":
    asyncio.run(main())