public class Overloading{
    // public void m1(){
    //     System.out.println("No-args m1");
    // }

    // public int m1(int i){
    //     System.out.println("int args m1");
    //     return i;
    // }

    public static void m1(){
        System.out.println("Parent m1 method");
    }

    public void m1(int i){
        System.out.println("m1 int...");
    }

    public int m1(float f){
        System.out.println("m1 float method...");
        return 1;
    }
}

class Child extends Overloading{
    public void m1(){
        System.out.println("static child m1...");
    }
}

class Test{
    public static void main(String[] args) {
        Overloading o = new Overloading();
        // o.m1();
        // o.m2();

        o.m1(10);
        o.m1(10.0f);

        Child c = new Child();
        c.m1();
    }
}