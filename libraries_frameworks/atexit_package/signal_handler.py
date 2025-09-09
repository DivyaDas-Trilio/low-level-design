import signal

def signal_cleanup(signum, frame):
    print("Cleaning Up via Signal Modules...{0}, {1}", signum, frame)
    import sys; sys.exit(0)
    
    
if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_cleanup)
    
    while True:
        pass