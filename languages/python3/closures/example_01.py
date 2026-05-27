def outer():
    x = 10
    def inner():
        print(x)
        print("Inner function")
    return inner    


print(outer().__closure__)