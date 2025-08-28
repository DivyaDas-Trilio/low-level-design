import threading, time

l = threading.Semaphore(2) # semaphores are based on lock mechanism not RLock
def semaphore(name):
    if l.acquire(blocking=False):
        # print(f'Value:- {val}')
        for i in range(10):
            time.sleep(0.5)
            print(f'Name:- {name}')
        l.release()
    else:
        print('Not acquired.')

t1 = threading.Thread(target=semaphore, args=('Dhoni',))
t2 = threading.Thread(target=semaphore, args=('Kohli',))
t3 = threading.Thread(target=semaphore, args=('Rohit',))

t1.start()
t2.start()
t3.start()

t1.join()
t2.join()
t3.join()

    