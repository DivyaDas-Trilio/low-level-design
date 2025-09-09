import atexit


@atexit.register
def cleanup():
    print("cleaning up Resources...")
    
    
if __name__ == "__main__":
    import sys; sys.exit()
    # while True:
    #     pass