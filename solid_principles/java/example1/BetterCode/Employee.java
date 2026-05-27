public class Employee {

    private int id;
    private String name;

    public Employee(int id, String name) {
        this.id = id;
        this.name = name;

    }

    public int getId() {
        return this.id;
    }

    public int setId(int id) {
        this.id = id;
    }

    public int getName() {
        return this.name;
    }

    public int setName(int name) {
        this.name = name;
    }

}

// This class resposible for getters and setters for Employee.
// Single Resposnibility.
