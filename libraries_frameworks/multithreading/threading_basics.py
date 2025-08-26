import threading as th
from time import sleep
import time
from threading import Thread

# Here, we can clearly see if task is Cpu bound then PVM is not executing tasks in parallel due to GIL.

def keep_printing(n):
    print(th.current_thread())
    for i in range(n):
        sleep(2)
        #print(f"keep printing {i}")
        print(i**i)

def main():
    import os
    print(os.getpid())
    print(th.current_thread())
    t1 = Thread(target=keep_printing, args=(20,))
    t2 = Thread(target=keep_printing, args=(20,))
    t3 = Thread(target=keep_printing, args=(20,))
    
    t1.start()
    t2.start()
    t3.start()
    
    t1.join()
    t2.join()
    t3.join()
    
    
if __name__ == '__main__':
    start = time.time()
    main()
    end = time.time()
    print(f'Elapsed Time= {end-start}')