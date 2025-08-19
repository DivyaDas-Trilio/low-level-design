from tokenize import String


def data_types():
    i: int = 10;
    f: float = 10.5
    c: complex = 10+20j
    b: bool = True
    s: str = "Test"
    
    print("Int:- {0}, {1}".format( i, type(i)))
    print("Float:- {0}, {1}".format( f, type(f)))
    print("Complex:- {0}, {1}".format( c, type(c)))
    print("Bool:- {0}, {1}".format( b, type(b)))
    print("Str:- {0}, {1}".format( s, type(s)))
    
if __name__ == '__main__':
    data_types()