import threading, time

# l = threading.Lock()
l = threading.RLock() # helpful in recursive method, and avoids deadlock.

def print_name(name):
    l.acquire()
    #l.acquire() # for normal lock, we cannot acquire multiple times same lock
    for i in range(10):
        l.acquire()
        time.sleep(0.5)
        print(f'Name:- {name}')
        l.release()
    l.release()

t1 = threading.Thread(target=print_name, args=('Dhoni',))
t2 = threading.Thread(target=print_name, args=('Kohli',))
t3 = threading.Thread(target=print_name, args=('Rohit',))

t1.start()
t2.start()
t3.start()

t1.join()
t2.join()
t3.join()