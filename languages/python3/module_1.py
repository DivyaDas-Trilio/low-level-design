class C0:
    def __init__(self):
        print('Constructor of C0.')
        self.i = 10
        self._i1 = 11
        self.__i2 = 12
    
class _C1:
    def __init__(self):
        print('Constructor of C1.')
        self.i = 10
        self._i1 = 11
        self.__i2 = 12
    
class __C2:
    def __init__(self):
        print('Constructor of C2.')
        self.i = 10
        self._i1 = 11
        self.__i2 = 12
        

if __name__ == '__main__':
    c0 = C0()
    print(c0.i, c0._i1)
    c1= _C1()
    print(c1.i, c1._i1)
    c2 = __C2()
    print(c2.i, c2._i1)