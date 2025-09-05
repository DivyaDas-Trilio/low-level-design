public class Overloading{
    // public void m1(){
    //     System.out.println("No-args m1");
    // }

    // public int m1(int i){
    //     System.out.println("int args m1");
    //     return i;
    // }

    private String str1;
    private int i;

    public void m1(){
        System.out.println("Parent m1 method");
    }

    public int m2(){
        System.out.println("Parent m2 method.");
        return 1;
    }

    public void m1(int i){
        System.out.println("m1 int...");
    }

    public int m1(float f){
        System.out.println("m1 float method...");
        return 1;
    }
}

class Test{
    public static void main(String[] args) {
        Overloading o = new Overloading();
        o.m1();
        o.m2();

        o.m1(10);
        o.m1(10.0f);
    }
}