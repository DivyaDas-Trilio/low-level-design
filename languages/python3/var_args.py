def m1(*args, **kwargs):
    print(type(args)) # tuple
    print(type(kwargs)) # Dict
    
    # print
    print(args)
    print(kwargs)
    
if __name__ == '__main__':
    m1(10,20,30,40,50, name='dj', roll=123, lst=(10,))