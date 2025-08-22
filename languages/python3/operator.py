def operator():
    # There is no such concept of increment/decrement unary operator in python.
    # Arithmetic oerators +, -, *, /, //, %
    n1, n2 = 10, 20
    print(n1+n2)
    print(n1-n2)
    print(n1*n2)
    print(n1/n2)
    print(n1//n2)
    print(n1%n2)
    
    # concatenation operator
    print(10+20) # Arithmetic
    print("10"+"20") # string concat , not efficient as creates new string everytime
    print([1,2]+[3,4]) # list concat
    #print(10+"20") # Not supported in python unlike java.
    print("10".join("20")) # for efficiency
    
    #  Relational Operator, > >= < <= == !=
    # Logical operators, &&, ||, !, ^
    # Assignment Operator, =
    # Ternary Operator ? : -> Not supported in python, but can be implemented using if else
operator()