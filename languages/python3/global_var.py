test = 10
"""
# case-01
def f1():
    print(test) # 10, since trying to access global var.

def f2():
    print(10) # 10, since trying to print global var
"""    
"""
def f1():
    test = 20 # this is local variable created in stack, and have highest priority
    print(test)
    
def f2():
    print(test) # this refers to globals var only.
"""
"""
If the change is intended for global var, not for local variable, then PVM gives us the global keyword to achieve this.
def f1():
    global test
    test=20
    print(test)
    
def f2():
    print(test)
""" 
# If req is to have same variable name both as global and local and changes in function need to have local variable aswell.
# then PVM provide us the globals() method, which conatins all the global variables in dict format and we can make use of that.   
def f1():
    test = 30
    print(test)
    globals()['test'] = 40
    
def f2():
    print(test)

if __name__ == '__main__':
    f1()
    f2()