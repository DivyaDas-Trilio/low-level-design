from concurrent.futures import ThreadPoolExecutor, as_completed
import time

def worker(n):
    print(f'sleeping: {n}')
    time.sleep(10)

def main():
    # Create a thread pool with 3 workers
    with ThreadPoolExecutor(max_workers=3) as executor:
        import pdb; pdb.set_trace()
        futures = [executor.submit(worker, i) for i in range(5)]
        executor.shutdown()

if __name__ == "__main__":
    main()
