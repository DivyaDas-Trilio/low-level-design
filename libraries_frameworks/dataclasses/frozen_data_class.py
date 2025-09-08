from dataclasses import dataclass


@dataclass(frozen=True)
class Person:
    name: str
    age: int
    
    
p1 = Person("DJ", 31)
print(p1)

p1.name= 'hii'