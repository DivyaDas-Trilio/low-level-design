def test():
    print("start")
    yield 1
    print("Middle")
    yield 2
    print("End")
    yield 3
    
test()