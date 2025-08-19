class Test:
    school_name = "HIT"
    def __init__(self):
        pass
    
t1 = Test()
t2 = Test()

# if only one copy is getting created for class var, then id of below should be same.
print(id(Test.school_name))
print(id(t1.school_name))
print(id(t2.school_name))

# if any changes is done on class var, then should be reflected jto all.
Test.school_name = "St.Stephens"
print(Test.school_name)
print(t1.school_name)
print(t2.school_name)

# We should avoid using object ref to access/modify class level variables.