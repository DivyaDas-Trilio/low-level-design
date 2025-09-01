import time
import threading

def consume(c):
    c.acquire()
    print('consumer acuired condition.')
    print('consumer waiting...')
    c.wait()
    print('consumer waiting completed!!')
    c.release()
    print('consumer relkeasing!!')
    print('consumer Exiting...')
    

def produce(c):
    time.sleep(2)
    print('producer waking up...')
    c.acquire()
    print('producer acuired condition')
    print('producer sleeping again!!')
    time.sleep(5)
    print('producer waking up again!!')
    c.notify()
    print('producer notifying.')
    c.release()
    print('producer relaesing condition object.')


c = threading.Condition()

t1 = threading.Thread(target=consume, args=(c,))
t2 = threading.Thread(target=produce, args=(c,))

t1.start()
t2.start()