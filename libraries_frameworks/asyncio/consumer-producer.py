import queue
import threading
import time

def producer(q):
    for i in range(1,6):
        time.sleep(0.5)
        item = f"Item-{i}"
        q.put(item)
        print(f"Produced {item}")
    q.put(None)

def consumer(q):
    while True:
        item = q.get()
        if item is None:
            break
        time.sleep(0.5)
        print(f"consumed {item} ")

def main():
    start = time.time()
    q = queue.Queue()
    t1 = threading.Thread(target=producer, args=(q,))
    t2 = threading.Thread(target=consumer, args=(q,))
    
    t1.start()
    t2.start()
    
    t1.join()
    t2.join()
    end = time.time()
    
    print(f'Elapsed Time:- {end-start}')
    
main()
    