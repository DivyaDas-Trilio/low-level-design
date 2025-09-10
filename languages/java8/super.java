class Super {
    Super(){
        System.out.println("Parent Constructor.");
    }

}

class Child extends Super{
    Child(){
        //super();
        System.out.println("Child Constructor.");
    }
}

class Test{
    public static void main(String[] args) {
        Child c = new Child();
    }
}
