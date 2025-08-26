from multiprocessing import Process

class MyMP(Process):
    def __init__(self):
        super().__init__()
        print('constructor.')
        
    def run(self):
        print('run...')
   
   
if __name__ == '__main__':      
    p1 = MyMP()
    p1.start()