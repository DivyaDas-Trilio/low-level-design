import os, time

task_q = []
def task_1(filename):
    with open(filename) as f:
        value = f.readlines()
        int_list = list(map(int, [x.strip() for x in value]))
        for each in int_list:
            time.sleep(0.5)
            task_q.append(each)
        
def task_2():
        time.sleep(1)
        while(len(task_q) > 0):
            value = task_q.pop()
            for i in range(int(value)):
                print(value )
            print("----"+str(value)+"------")
    
if __name__ == '__main__':
    start = time.time()
    filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'testcase')
    task_1(filename); task_2()
    end = time.time()
    print('Elapsed Time:- ', end- start )