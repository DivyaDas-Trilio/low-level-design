import threading
import time

def traffic_police(e):
    while True:
        print("RED LIGHT...")
        time.sleep(10)
        print("GREEN LIGHT...")
        e.set()
        time.sleep(20)
        e.clear()
        
 

