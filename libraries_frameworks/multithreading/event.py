import threading, time

e = threading.Event()

def traffic_police(e):
    while True:
        time.sleep(5)
        print('event condition is True.')
        e.set()
        time.sleep(10)
        e.clear()
    

def driver(e):
    while True:
        if(e.isSet()):
            print('driver is moving...')
        else:
            print('waiting for event to set true.')
            e.wait()


if __name__ == '__main__':
    t1 = threading.Thread(target=traffic_police, args=(e,))
    t2 = threading.Thread(target=driver, args=(e,))
    
    t1.start()
    t2.start()
    
    t1.join()
    t2.join()