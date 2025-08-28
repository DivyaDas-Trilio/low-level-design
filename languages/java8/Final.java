public class Final {
    public static void main(String[] args) {
        final int i = 10;
        System.out.println(i);
        //i = 20;
        System.out.println(i);
    }
}

// final class A{

// }

// class B extends A {

// }

class P{
    public final void m1(){

    }

}

class C extends P{
    //public void m1(){

    //}

}


class Test{
    public final int x;
    int j;
    Test(){
        this.x=10;
        j=11;
        this.j = 20;
    }
}
