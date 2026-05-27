import threading


def cpu_bound_task(num):
    while num:
        num -= 1

if __name__ == "__main__":
    t1 = threading.Thread(target=cpu_bound_task, args=(10000000000,))
    t1.start()
    t1.join()