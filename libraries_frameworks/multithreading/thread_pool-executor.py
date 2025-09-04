# Executor Class is  the BASE Abstract Class, which has abstract methods of map(), submit(), shutdown()

#ThreadPoolExecutor and ProcessPool Executor extends Abstract Class.

from concurrent.futures import ThreadPoolExecutor
from threading import Thread
import time

def fn_sleep(delay):
    print('sleeping...')
    time.sleep(delay)
    #raise ValueError('value error')
    return delay

if __name__ == '__main__':
    th = ThreadPoolExecutor(1)
    #submit method for one set of args.
    # future = th.submit(fn_sleep, 5)
    # print(future.result()) # its the result which blocks the main thread., if we do not provide this main thread wont be blocked.
    # print(future.done())
    # print('main thread ...')
    
    # map method for multiple set of args.
    delay = [5, 5, 5]
    futures = th.map(fn_sleep, delay)
    print('In Main method by main thread...')
    for f in futures:
        print(f)
    # print(futures)
    print('Ending Main Thread...')