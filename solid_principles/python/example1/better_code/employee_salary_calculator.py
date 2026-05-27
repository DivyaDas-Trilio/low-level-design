from employee import Employee
class EmployeeSalaryCalculator:
    def __init__(self, emp: Employee, base_salary: float, bonus_percentage: float):
        self.base_salary = emp.get_employee_salary()
        self.bonus_percentage = bonus_percentage

    def calculate_bonus(self):
        return self.base_salary * (self.bonus_percentage / 100)

    def calculate_total_salary(self):
        return self.base_salary + self.calculate_bonus()
    
    