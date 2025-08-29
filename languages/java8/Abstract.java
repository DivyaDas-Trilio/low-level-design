interface I{

}

abstract class Abstract implements I{
    abstract void m1();
    abstract void m2();
}

abstract class S1 extends Abstract{
    void m1(){};
}

abstract class S2 extends S1{
    void m2(){};
}
