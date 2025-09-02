from multiprocessing import Process, current_process
import multiprocessing
import time

def func1():
    print('Global func1...')
    time.sleep(3)
    print(current_process().is_alive())


if __name__ == '__main__':
    p1 = Process(target=func1)
    p1.start()
    print(multiprocessing.active_children())
    print(current_process().name)
    p1.name = 'dj'
    print(p1.name)
    p1.join()
    print(p1.is_alive())