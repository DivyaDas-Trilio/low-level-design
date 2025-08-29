from threading import Event, Thread
from producer import traffic_police
from consumer import consumer

if __name__ == '__main__':
    e: Event = Event()
    t1 = Thread(target=traffic_police, args=(e,))
    t2 = Thread(target=consumer, args=(e,))
    t1.start()
    t2.start()
    