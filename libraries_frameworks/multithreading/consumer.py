import threading
import time

def consumer(e):
    while True:
        if(e.is_set()):
            print('DRIVING...')
            time.sleep(20)
        else:
            print("WAITING FOR GREEN LIGHT...")
            e.wait()
            time.sleep(10)
        
    