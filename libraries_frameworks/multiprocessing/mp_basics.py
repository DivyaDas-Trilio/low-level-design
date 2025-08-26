import multiprocessing as mp
from multiprocessing import Process
import time
from time import sleep

# Here, we saw tasks are executing in parallel with multiprocessing.

def keep_printing(n):
    print(mp.current_process())
    for i in range(n):
        sleep(0.5)
        #print(f'I am Keep_printing {i}')
        print(i**i)

def main():
    print(mp.current_process())
    
    p1 = Process(target=keep_printing, args=(20,))
    p2 = Process(target=keep_printing, args=(20,))
    p3 = Process(target=keep_printing, args=(20,))
    #p4 = Process(target=keep_printing, args=(20,))
    p1.start()
    p2.start()
    p3.start()
    #p4.start()
    p1.join()
    p2.join()
    p3.join()
    #p4.join()
        
if __name__ == '__main__':
    start = time.time()
    main()
    end = time.time()
    print(f'Elapsed Time:- {end-start}')