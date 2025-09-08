from dataclasses import dataclass

@dataclass
class Person:
    name: str
    age: int
    
@dataclass
class Employee(Person):
    emp_id: str
    emp_dept: str
    

e1 = Employee('dj', 31, "123", "CSE")
print(e1)