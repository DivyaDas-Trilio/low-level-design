public class Overloading{
    public void m1(){
        System.out.println("No-args m1");
    }

    public int m1(int i){
        System.out.println("int args m1");
        return i;
    }
}

class Test{
    public static void main(String[] args) {
        Overloading o = new Overloading();
        o.m1();
        o.m1(10);
    }
}