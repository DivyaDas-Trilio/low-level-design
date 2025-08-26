from threading import Thread

class MyThread(Thread):
    def __init__(self):
        super().__init__()
        print('constructor...')
        
    def run(self):
        print('Run Method...')
        

if __name__ == '__main__':
    t1 = MyThread()
    t1.start()
    t1.join()