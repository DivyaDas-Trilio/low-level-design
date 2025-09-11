class ParentConst{

    public ParentConst(){
        System.out.println("Parent constructor...");
    }
    ParentConst(int num){
        System.out.println(num);
    }
}


public class constructor extends ParentConst{

    public constructor(){
        super(20);
        //this(10);
        System.out.println("Default Constructor...");
    }

    public constructor(int n){
        System.out.println(n);
    }


    
}



class Main{
    public static void main(String[] args) {
        constructor c = new constructor();
    }
}
