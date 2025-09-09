class MyContextManager:
    def __init__(self):
        print("init...")
    
    def __enter__(self):
        print("Enter ...")
        
    def __exit__(self, exc_type, exc__value, traceback):
        print("Exit...")
        
        
# from contextlib import AbstractContextManager

# class MyContextManager(AbstractContextManager):
#     def __init__(self):
#         print('ionit..')
        
#     def __exit__(self, exc_type, exc_value, traceback):
#         print('exit...')
    

if __name__ == "__main__":
    with MyContextManager() as cntx:
        print('inside context manager...')