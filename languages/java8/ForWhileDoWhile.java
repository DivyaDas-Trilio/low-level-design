public class ForWhileDoWhile {
    public static void main(String[] args) {
        for(int i=0; i<10;i++){
            System.out.println(i);
        }

        String[] months = {"Jan", "Feb", "Marc"};
        for(String month: months){
            System.out.println(month);
            // if(month.equals("Feb"))
            //     break; // stop executing loop, come out of it.
            if(month.equals("Feb")) continue;
            System.out.println("Rest code...");
        } 
        int num = 0;
        while(num<10){
            System.out.println(num);
            num++;
        }
        int num2 = 0;
        do{
            System.out.println("Printing"+ num2);
            num2++;
        }while(num2<10);
    }
    
}
