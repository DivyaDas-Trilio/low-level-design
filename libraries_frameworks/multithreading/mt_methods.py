import threading

def func1():
    print('I am Func1...')
    print(threading.current_thread())
    print(threading.current_thread().ident)
    
if __name__ == '__main__':
    t1 = threading.Thread(target=func1)
    t1.setName('MyThread-01')
    t1.start()
    print(threading.active_count())
    print(t1.name)
    t1.name = 'dj'
    print(t1.name)
    print(threading.current_thread())
    print(threading.current_thread().ident)
    