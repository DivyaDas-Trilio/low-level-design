
def logg(func):
    def wrapper(*args, **kwargs):
        print('Logg Enter...')
        func(*args, **kwargs)
        print('Logg Ends...')
    return wrapper

def super_logg(num):
    def decorator(func):
        def wrapper(*args, **kwargs):
            print("super logg Enters...")
            for _ in range(num):
                func(*args, **kwargs)
            print("super logg Ends...")
        return wrapper
    return decorator

def greet(name):
    print(f"Hello...{name}")
        

super_logg(3)(logg(greet))("Dj")

#greet("Divya")