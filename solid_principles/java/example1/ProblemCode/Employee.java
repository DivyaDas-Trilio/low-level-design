
public class Employee {
    private int id;
    private String name;

    public Employee(int id, String name) {
        this.id = id;
        this.name = name;
    }

    public double getEmployeeSalary() {
        return 1000.0;
    }

    public void printPerformanceReport() {
        System.out.println("Performance Report.");
    }

    public void updateEmployeeData() {
        System.out.println("Updation of Employee Data.");
    }

    public void fetchEmployeeData() {
        System.out.println("Employee Details.");
    }
}

// what is the issue with above class.
// issue1:- This class has many responsibilities.
// It does gettters and setters
// It does printing responsibility.
// It does updation
