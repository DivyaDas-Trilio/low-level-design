from typing import Final, final

class Parent:
    def __init__(self):
        print("Parent Constructor...")
     
    @final
    def m1(self):
        print("Parent m1 method.")

class Child1(Parent):
    # def __init__(self):
    #     print("Child Constructor...")
        
    def m1(self):
        print("child m1 method")

if __name__ == "__main__":
    p = Parent()
    p.m1()
    
    c = Child1()
    c.m1()