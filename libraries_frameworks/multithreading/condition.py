import threading, time

c = threading.Condition()
lst = []

def consumer(c):
    while True:
        c.acquire()
        c.wait()
        print(lst)
        c.release()
        time.sleep(3)

def producer(c):
    while True:
        c.acquire()
        import random
        num = random.randint(10,100)
        time.sleep(1)
        lst.append(num)
        c.notify()
        c.release()
        time.sleep(3)

if __name__ == '__main__':
    t1 = threading.Thread(target=producer, args=(c,))
    t2 = threading.Thread(target=consumer, args=(c,))
    
    t1.start()
    t2.start()
    
    t1.join()
    t2.join()