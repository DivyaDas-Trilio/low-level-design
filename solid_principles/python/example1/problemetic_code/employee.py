from typing import List, Any

"""
This class has issues, 
what is the issue:-
1. This class is doing too many things.
2. 
"""

class Employee:
    __id: int
    __name: str

    def __init__(self, id, name):
        self.__id = id
        self.__name = name

    def print_performance_report(self, e: Employee) -> str:
        print('Performance Report of Employee:- {0}'.format(e))

    def compute_salary(self, e: Employee) -> float:
        print('salary of Employee.')

    def update_employee_data(self, e: Employee) -> bool:
        print('Employee Updation.')

    def fetch_employee_data(self, e: Employee) -> List[dict[str, Any]]:
        print('Fetched Employee Data.')



# Driver Code...
e1 = Employee(1, 'dj')
print(e1.id)