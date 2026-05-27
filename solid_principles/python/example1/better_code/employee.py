
class Employee:
    __id: int
    __name: str

    def __init__(self, id, name):
        self.__id = id
        self.__name = name
        self.__salary = 1000.0  # Default salary

    def get_employee_id(self):
        return self.__id
    
    def get_employee_name(self):
        return self.__name
    
    def get_employee_salary(self):
        return self.__salary
    
    def set_employee_salary(self, salary):
        self.__salary = salary
        return self.__salary
    
    def set_employee_id(self, id):
        self.__id = id
        return self.__id
    
    def set_employee_name(self, name):
        self.__name = name
        return self.__name
    
    