from multiprocessing import Process
from operator import mul
import time

def multiply(num):
    for i in range(num):
        return num**num

if __name__ == '__main__':
    start = time.time()
    p1 = Process(target=multiply, args=(1000000,))
    p2 = Process(target=multiply, args=(1000000,))
    p1.start()
    p2.start()
    p1.join()
    p2.join()
    
    end = time.time()
    print(f'Result:- {end-start}')
    
    