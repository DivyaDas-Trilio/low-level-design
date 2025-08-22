class FlowControl{
    public static void ifElseLadder(){
        boolean isSchoolOpen =true;
        if(isSchoolOpen){
            System.out.println("I will go to school.");
        }
        else if(true){
            System.out.print("I wont go School.");
        }
    }
    public static void main(String[] args) {
        FlowControl.ifElseLadder();
    }
}