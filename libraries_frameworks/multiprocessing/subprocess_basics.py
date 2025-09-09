from os import pipe
import subprocess

proc = None

def process_1():
    proc = subprocess.Popen(
        ["dd","if=/dev/urandom", "of=test.txt", "bs=1K", "count=1M", "status=progress"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr= subprocess.PIPE
    )
    print(proc.stdout)
    #print(proc.stdin)
    #out, err = proc.communicate()
    #print(out)
    #print(err)
    
    while True:
        res = proc.poll()
        if res is None:
            print('Process still Running...')
        else:
            print('Process has Exited!!.')
            break

def process_2():
    pass

if __name__ == "__main__":
    # process_1()
    process_1()
    #print(out, err)
    