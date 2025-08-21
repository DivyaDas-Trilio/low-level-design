class VarArgs{
    public static void main(String[] args) {
        VarArgs va = new VarArgs();
        va.multipleArgs(10,20,30,40,50,60,70,80,90);
    }

    public void multipleArgs(int num, int... args){
        System.out.println("Num:- "+num);
        for(int i=0; i<args.length;i++)
            System.out.println(args[i]);
    }
}