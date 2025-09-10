public class StaticBlock {
    static int j = 20; 
    static {
        int i = 10;
        System.out.println("Static Block 1...");
        System.out.println("i:- "+ j);
        m1();
    }

    public static void m1(){
        System.out.println("i:- "+j);
    }

    public static void main(String[] args) {
        System.out.println("Main method..");
    }
}
