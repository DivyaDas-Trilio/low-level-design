public class ExceptionHandling {
    public static void main(String[] args) {
        System.out.println("stme-01");
        try{
            System.out.println(10/0);
        }
        catch(ArithmeticException ex){
            System.out.println(10/2);
        }
        System.out.println("stmt-03");
    }
}
