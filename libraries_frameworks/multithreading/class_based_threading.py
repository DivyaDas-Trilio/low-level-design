from concurrent.futures import thread
from threading import Thread
import threading

class MyThread(Thread):
    def __init__(self):
        super().__init__()
        print('constructor...')
        
    def run(self):
        print('Run Method...')
        

if __name__ == '__main__':
    t1 = MyThread()
    t2 = MyThread()
    t3 = MyThread()
    t1.start()
    t2.start()
    t3.start()
    l = threading.enumerate()
    for each in l:
        print(each.name)