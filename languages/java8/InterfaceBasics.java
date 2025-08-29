public interface InterfaceBasics {

    void m1();
    void m2();
}

abstract class Service1 extends A implements InterfaceBasics{
    public void m1(){};

}

class A{

}

class B extends A{

}

class C extends B implements Service1{

}