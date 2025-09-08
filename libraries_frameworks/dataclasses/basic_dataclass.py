class Person:
    def __init__(self, name, age):
        self.name: int = name 
        self.age: int = age
        
    def __repr__(self):
        return "Person"

class Employee(Person):
    def __init__(self, name, age, emp_id, dept):
        super().__init__(name, age)
        self.emp_id: str = emp_id
        self.dept: str = dept
        
    def __repr__(self):
        return "Child"+super().__repr__()
    
    def __getattribute__(self, name):
        print("Getters...")
        return super().__getattribute__(name)
    
    def __getattr__(self, value):
        print('getatr,...')
        return self.value
        
        
emp = Employee("dj", 31, 123, 'cse')
print(emp.__dict__)
print(emp.nam)