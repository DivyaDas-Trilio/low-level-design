import threading

counter = 10

def increment():
    global counter
    counter += 1
        
def decrement():
    global counter
    counter -= 1
        
t1 = threading.Thread(target=increment)
t2 = threading.Thread(target=decrement)

t1.start()
t2.start()

t1.join()
t2.join()

print(f'Final counter = {counter}')