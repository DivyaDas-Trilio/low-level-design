from module_1 import C0, _C1, __C2

class Child(C0):
    def __init__(self):
        super().__init__()
        print('Child COnstructor.')

if __name__ == '__main__':
    c0 = C0()
    print(c0.i, c0._i1)
    c1= _C1()
    print(c1.i, c1._i1)
    c2 = __C2()
    print(c2.i, c2._i1)
    
    ch = Child()
    print(ch.i, ch._i1, ch.__i2)